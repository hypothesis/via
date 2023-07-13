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
    def __init__(self, api_key: str):
        self._api_key = api_key

        session = requests.Session()
        session.headers["Accept-Language"] = "en-US"
        self._http = HTTPService(session=session)

    def canonical_video_url(self, video_id: str) -> str:
        """
        Return the canonical URL for a YouTube video.

        This is used as the URL which YouTube transcript annotations are
        associated with.
        """
        escaped_id = quote_plus(video_id)
        return f"https://www.youtube.com/watch?v={escaped_id}"

    def get_video_info(self, video_id: str) -> Video:
        response = self._http.post(
            f"https://youtubei.googleapis.com/youtubei/v1/player?key={self._api_key}",
            json={
                "context": {
                    "client": {
                        "hl": "en",
                        "clientName": "WEB",
                        # Suspicious value right here...
                        "clientVersion": "2.20210721.00.00",
                    }
                },
                "videoId": video_id,
            },
        )

        return Video.from_json(
            url=self.canonical_video_url(video_id), data=response.json()
        )

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
