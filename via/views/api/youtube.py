import logging
from dataclasses import asdict

from pyramid.view import view_config

from via.services import YouTubeService

logger = logging.getLogger(__name__)


@view_config(
    route_name="api.youtube.transcript",
    request_method="GET",
    permission="api",
    renderer="json",
)
def get_transcript(request):
    """Return the transcript of a given YouTube video."""

    video_id = request.matchdict["video_id"]
    caption_track_id = request.matchdict["caption_track_id"]

    transcript = request.find_service(YouTubeService).get_transcript(video_id, caption_track_id=caption_track_id)

    return {
        # Ideally this return value would be vert close to asdict(transcript)
        # instead of there being a lot of mapping
        "data": {
            "type": "transcripts",
            "id": video_id,
            "attributes": {"segments": asdict(transcript)["text"]},
        }
    }
