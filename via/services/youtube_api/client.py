import json
import re
from html import unescape
from urllib.parse import quote_plus
from xml.etree import ElementTree

import requests

from via.services import HTTPService
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


class YouTubeAPIClient:
    def __init__(self):
        self._http_session = requests.Session()
        self._http_session.headers["Accept-Language"] = "en-US"
        self._http = HTTPService(session=self._http_session)

    def canonical_video_url(self, video_id: str) -> str:
        """
        Return the canonical URL for a YouTube video.

        This is used as the URL which YouTube transcript annotations are
        associated with.
        """
        escaped_id = quote_plus(video_id)
        return f"https://www.youtube.com/watch?v={escaped_id}"

    def get_video_info(self, video_id: str) -> Video:
        url = self.canonical_video_url(video_id)
        html = self._get_html(url)

        # It might be nice to do something less horrible here, like using
        # beautiful soup to find all script tags (which is where this comes
        # from)
        start_chars = ">var ytInitialPlayerResponse = "
        try:
            start = html.index(start_chars)
        except ValueError:
            # The placement here is weird. Should we check for this first in
            # _get_html or can we get the info we need _and_ get captcha'd
            # sometimes?
            if 'class="g-recaptcha"' in html:
                raise YouTubeAPIError("too_many_requests", video_id)

            raise YouTubeAPIError("unexpected_json_format", video_id)

        end = html.index("};", start)
        video_info = html[start + len(start_chars) : end + 1]

        return Video.from_json(url=url, data=json.loads(video_info))

    def get_transcript(self, caption_track: CaptionTrack) -> Transcript:
        response = self._http.get(url=caption_track.url)
        xml_elements = ElementTree.fromstring(response.text)

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


    _COOKIE_REGEX = re.compile(r'name="v" value="(.*?)"')

    def _get_html(self, url, retry_on_consent=True):
        response = self._http.get(url=url)
        html = unescape(response.text)

        if 'action="https://consent.youtube.com/s"' not in html:
            return html

        # Looks like we are being asked for Cookie permission
        if retry_on_consent and (match := self._COOKIE_REGEX.search(html)):
            self._http_session.cookies.set(
                "CONSENT", "YES+" + match.group(1), domain=".youtube.com"
            )
            return self._get_html(url, retry_on_consent=False)

        raise YouTubeAPIError("failed_to_create_consent_cookie", url)
