from urllib.parse import parse_qs, quote_plus, urlparse

from via.exceptions import BadURL
from via.services.youtube_api import Transcript
from via.services.youtube_api.client import Video, YouTubeAPIClient


class YouTubeServiceError(Exception):
    ...


class YouTubeService:
    def __init__(self, enabled: bool, api_client: YouTubeAPIClient):
        self._enabled = enabled
        self._api_client = api_client

    @property
    def enabled(self):
        return self._enabled

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

    def get_video_info(self, video_id=None, video_url=None) -> Video:
        if video_url:
            video_id = self.get_video_id(video_url)

        if not video_id:
            raise BadURL(f"Unsupported video URL: {video_url}", url=video_url)

        video = self._api_client.get_video_info(video_id=video_id)

        if not video.is_playable:
            raise YouTubeServiceError("video_unavailable", video_id)

        return video

    def get_transcript(self, video_id, caption_track_id) -> Transcript:
        video = self.get_video_info(video_id)

        if not video.has_captions:
            raise YouTubeServiceError("no_transcripts_available", video_id)

        for caption_track in video.caption.tracks:
            if caption_track.id == caption_track_id:
                return self._api_client.get_transcript(caption_track)

        raise YouTubeServiceError("cannot_find_transcript", video_id, caption_track_id)


def factory(_context, request):
    enabled = request.registry.settings["youtube_transcripts"]

    return YouTubeService(
        enabled=enabled,
        # Do not use the global HTTPService, as we will pollute the
        # session with cookie information as a part of getting info
        api_client=YouTubeAPIClient(request.registry.settings["youtube_api_key"])
        if enabled
        else None,
    )
