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
    """Something has gone wrong interacting with YouTube."""


class YouTubeAPIClient:
    """A client for interacting with YouTube and manipulating related URLs."""

    def __init__(self):
        session = requests.Session()
        # Ensure any translations that Google provides are in English
        session.headers["Accept-Language"] = "en-US"
        self._http = HTTPService(session=session)

    def get_video_info(self, video_id: str) -> Video:
        """Get information for a given YouTube video."""

        response = self._http.post(
            "https://youtubei.googleapis.com/youtubei/v1/player",
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

        return Video.from_v1_json(data=response.json())

    def get_transcript(self, caption_track: CaptionTrack) -> Transcript:
        """Get the transcript associated with a caption track.

        You can set the track `translated_language_code` to ensure we translate
        the value before returning it.
        """

        if not caption_track.url:
            raise ValueError("Cannot get a transcript without a URL")

        response = self._http.get(url=caption_track.url)
        xml_elements = ElementTree.fromstring(response.text)

        return Transcript(
            track=caption_track,
            text=[
                TranscriptText(
                    text=self._strip_html(xml_element.text),
                    start=float(xml_element.attrib["start"]),
                    duration=float(xml_element.attrib.get("dur", "0.0")),
                )
                for xml_element in xml_elements
                if xml_element.text is not None
            ],
        )

    @staticmethod
    def _strip_html(xml_string):
        """Remove all non-text content from an XML fragment or string."""

        return "".join(
            ElementTree.fromstring(f"<span>{xml_string}</span>").itertext()
        ).strip()
