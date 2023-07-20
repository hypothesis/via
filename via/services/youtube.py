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

    def get_video_info(
        self, video_id=None, video_url=None, with_captions=False
    ) -> Video:
        if video_url:
            video_id = self._api_client.parse_video_url(video_url)

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
