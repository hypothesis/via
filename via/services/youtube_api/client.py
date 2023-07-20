from typing import Optional
from urllib.parse import parse_qs, urlparse
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

    def __init__(self, api_key):
        self._api_key = api_key
        session = requests.Session()
        # Ensure any translations that Google provides are in English
        session.headers["Accept-Language"] = "en-US"
        self._http = HTTPService(session=session)

    def parse_video_url(self, url: str) -> Optional[str]:
        """Return the YouTube video ID from the given URL, or None."""

        parsed = urlparse(url)
        path_parts = parsed.path.split("/")

        # youtu.be/VIDEO_ID
        if parsed.netloc == "youtu.be" and len(path_parts) >= 2 and not path_parts[0]:
            return path_parts[1]

        if parsed.netloc not in ["www.youtube.com", "youtube.com", "m.youtube.com"]:
            return None

        query_params = parse_qs(parsed.query)

        # https://youtube.com?v=VIDEO_ID, youtube.com/watch?v=VIDEO_ID, etc.
        if "v" in query_params:
            return query_params["v"][0]

        path_parts = parsed.path.split("/")

        # https://yotube.com/v/VIDEO_ID, /embed/VIDEO_ID, etc.
        if (
            len(path_parts) >= 3
            and not path_parts[0]
            and path_parts[1] in ["v", "embed", "shorts", "live"]
        ):
            return path_parts[2]

        return None

    def get_video_info(self, video_id: str, with_captions: bool = False):
        if with_captions:
            return self._get_video_info_v1(video_id)

        response = self._http.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={
                "id": video_id,
                "key": self._api_key,
                "part": "snippet,contentDetails,status",
                "maxResults": "1",
            },
        )

        return Video.from_v3_json(data=response.json()["items"][0])

    def _get_video_info_v1(self, video_id: str) -> Video:
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
