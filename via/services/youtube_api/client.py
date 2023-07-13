import json
import re
from html import unescape
from xml.etree import ElementTree

from requests import HTTPError

from via.services.youtube_api.models import (
    CaptionTrack,
    Transcript,
    TranscriptText,
    Video,
)


class YouTubeAPIError(Exception):
    ...


def strip_html(string):
    return "".join(ElementTree.fromstring(f"<span>{string}</span>").itertext()).strip()


class YouTubeAPI:
    def __init__(self, http_session):
        self._http = http_session

    def get_video_info(self, video_id: str) -> Video:
        html = self._get_video_html(video_id)

        start_chars = ">var ytInitialPlayerResponse = "
        try:
            start = html.index(start_chars)
        except ValueError:
            if 'class="g-recaptcha"' in html:
                raise YouTubeAPIError("too_many_requests", video_id)

            raise YouTubeAPIError("unexpected_json_format", video_id)

        end = html.index("};", start)
        video_info = html[start + len(start_chars) : end + 1]

        return Video.from_json(json.loads(video_info))

    def get_transcript(self, caption_track: CaptionTrack) -> Transcript:
        xml_data = self._get_url(url=caption_track.url)
        xml_elements = ElementTree.fromstring(xml_data)

        return Transcript(
            track=caption_track,
            text=[
                TranscriptText(
                    text=strip_html(xml_element.text),
                    start=float(xml_element.attrib["start"]),
                    duration=float(xml_element.attrib.get("dur", "0.0")),
                )
                for xml_element in xml_elements
                if xml_element.text is not None
            ],
        )

    _WATCH_URL = "https://www.youtube.com/watch?v={video_id}"

    def _get_video_html(self, video_id, retry_on_consent=True):
        html = unescape(self._get_url(url=self._WATCH_URL.format(video_id=video_id)))

        if 'action="https://consent.youtube.com/s"' not in html:
            return html

        # Looks like we are being asked for Cookie permission
        if retry_on_consent and (match := re.search('name="v" value="(.*?)"', html)):
            self._http.cookies.set(
                "CONSENT", "YES+" + match.group(1), domain=".youtube.com"
            )
            return self._get_video_html(video_id, retry_on_consent=False)

        raise YouTubeAPIError("failed_to_create_consent_cookie", video_id)

    def _get_url(self, url):
        response = self._http.get(url, headers={"Accept-Language": "en-US"})

        try:
            response.raise_for_status()
            return response.text
        except HTTPError as error:
            raise YouTubeAPIError("unhandled_error", error)
