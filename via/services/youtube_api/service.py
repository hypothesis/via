from via.services import HTTPService
from via.services.youtube_api.client import YouTubeAPI
from via.services.youtube_api.exceptions import YouTubeServiceError
from via.services.youtube_api.models import Transcript, Video


class YouTubeAPIService:
    def __init__(self, api_client: YouTubeAPI):
        self.api_client = api_client

    def get_video_info(self, video_id) -> Video:
        video = self.api_client.get_video_info(video_id=video_id)

        if not video.is_playable:
            raise YouTubeServiceError("video_unavailable", video_id)

        return video

    def get_transcript(self, video_id, caption_track_id) -> Transcript:
        video = self.get_video_info(video_id)

        if video.has_captions:
            for caption_track in video.caption.tracks:
                if caption_track.id == caption_track_id:
                    return self.api_client.get_transcript(caption_track)

        raise YouTubeServiceError("no_transcript_available", video_id)


def service_factory(_context, _request):
    return YouTubeAPIService(
        # Do not use the global HTTPService, as we will pollute the
        # session with cookie information as a part of getting info
        api_client=YouTubeAPI(http_session=HTTPService())
    )
