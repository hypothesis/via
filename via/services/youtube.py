from urllib.parse import parse_qs, urlparse

from via.exceptions import BadURL
from via.services.youtube_api import CaptionTrack, Transcript, Video, YouTubeAPIClient


class YouTubeServiceError(Exception):
    """Something has gone wrong in the YouTube service itself."""


class YouTubeService:
    def __init__(self, enabled: bool, api_client: YouTubeAPIClient):
        self._enabled = enabled
        self._api_client = api_client

    @property
    def enabled(self):
        return bool(self._enabled and self._api_client)

    def get_video_id(self, url):
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

    def get_video_info(
        self, video_id=None, video_url=None, with_captions=False
    ) -> Video:
        if video_url:
            video_id = self.get_video_id(video_url)

        if not video_id:
            raise BadURL(f"Unsupported video URL: {video_url}", url=video_url)

        return self._api_client.get_video_info(
            video_id=video_id, with_captions=with_captions
        )

    def get_transcript(self, video_id: str, transcript_id: str) -> Transcript:
        video = self.get_video_info(video_id=video_id, with_captions=True)

        if caption_track := video.caption.find_matching_track(
            [CaptionTrack.from_id(transcript_id)]
        ):
            return self._api_client.get_transcript(caption_track)

        raise YouTubeServiceError(
            "no_matching_transcript_found", video_id, transcript_id
        )


def factory(_context, request):
    api_key = request.registry.settings["youtube_api_key"]

    return YouTubeService(
        enabled=request.registry.settings["youtube_transcripts"],
        api_client=YouTubeAPIClient(api_key=api_key) if api_key else None,
    )
