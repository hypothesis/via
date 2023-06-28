import logging

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

    transcript = request.find_service(YouTubeService).get_transcript(video_id)

    return {
        "data": {
            "type": "transcripts",
            "id": video_id,
            "attributes": {"segments": transcript},
        }
    }
