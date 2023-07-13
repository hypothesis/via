import json
import re
from html import unescape
from typing import List
from xml.etree import ElementTree

import requests
from requests import HTTPError

from via.services.youtube_transcript.models import TranscriptInfo, TranscriptText, Transcript


class YouTubeTranscriptError(Exception):
    ...


def strip_html(string):
    return "".join(ElementTree.fromstring(f"<span>{string}</span>").itertext()).strip()


class YouTubeAPI:
    def __init__(self, http_session):
        self._http = http_session

    def list_transcripts(self, video_id: str) -> List[TranscriptInfo]:
        html = self._get_video_html(video_id)

        html_parts = html.split('"captions":')

        if len(html_parts) <= 1:
            if 'class="g-recaptcha"' in html:
                raise YouTubeTranscriptError("too_many_requests", video_id)

            if '"playabilityStatus":' not in html:
                raise YouTubeTranscriptError("video_unavailable", video_id)

            raise YouTubeTranscriptError("transcript_disabled", video_id)

        captions_json = json.loads(
            html_parts[1].split(',"videoDetails')[0].replace("\n", "")
        ).get("playerCaptionsTracklistRenderer")

        if captions_json is None:
            raise YouTubeTranscriptError("transcript_disabled", video_id)

        if "captionTracks" not in captions_json:
            raise YouTubeTranscriptError("no_transcript_available", video_id)

        return [
            TranscriptInfo(
                id=caption_track["vssId"],
                language_code=caption_track["languageCode"],
                name=caption_track["name"]["simpleText"],
                is_auto_generated=caption_track.get("kind", "") == "asr",
                is_translatable=caption_track.get("isTranslatable", False),
                url=caption_track["baseUrl"],
            )
            for caption_track in captions_json["captionTracks"]
        ]

    def get_transcript(self, transcript_info: TranscriptInfo) -> Transcript:
        xml_data = self._get_url(url=transcript_info.url)
        xml_elements = ElementTree.fromstring(xml_data)

        return Transcript(
            info=transcript_info,
            text=[
                TranscriptText(
                    text=strip_html(xml_element.text),
                    start=float(xml_element.attrib["start"]),
                    duration=float(xml_element.attrib.get("dur", "0.0")),
                )
                for xml_element in xml_elements
                if xml_element.text is not None
            ]
        )

    _WATCH_URL = "https://www.youtube.com/watch?v={video_id}"

    def _get_video_html(self, video_id, retry_on_consent=True):
        html = unescape(
            self._get_url(
                url=self._WATCH_URL.format(video_id=video_id)
            )
        )

        if 'action="https://consent.youtube.com/s"' not in html:
            return html

        if retry_on_consent and (match := re.search('name="v" value="(.*?)"', html)):
            self._http.cookies.set(
                "CONSENT", "YES+" + match.group(1), domain=".youtube.com"
            )
            return self._get_video_html(video_id, retry_on_consent=False)

        raise YouTubeTranscriptError("failed_to_create_consent_cookie", video_id)

    def _get_url(self, url):
        response = self._http.get(url, headers={"Accept-Language": "en-US"})

        try:
            response.raise_for_status()
            return response.text
        except HTTPError as error:
            raise YouTubeTranscriptError("unhandled_error", error)


video_id = "qQ6a0iOzyHE"
video_id = "sHUYfz_T3L0"  # Coloured formatting?

api_client = YouTubeAPI(requests.Session())
html = api_client._get_video_html('HPI2jGvxEM4')

start_chars = '>var ytInitialXPlayerResponse = '
try:
    start = html.index(start_chars) + len(start_chars)
except ValueError:
    print("NO!")
    exit()

end = html.index('};', start) + 1
video_info = html[start: end]

print(video_info[:80])
print(video_info[-80:])
exit()

html_parts = html.split('>var ytInitialPlayerResponse = ', maxsplit=1)
print(len(html_parts))
html_parts = html_parts[1].split('};', maxsplit=1)
print(html_parts[0])
video_data = json.loads(html_parts[0] + '}')

with open('wat.json', 'w') as handle:
    json.dump(video_data, handle, indent=4)

exit()

for transcript_info in api_client.list_transcripts(video_id):
    print(transcript_info)
