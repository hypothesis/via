import logging

from h_pyramid_sentry import report_exception as report_exception_to_sentry
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

    try:
        transcript = request.find_service(YouTubeService).get_transcript(video_id)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        report_exception_to_sentry(exc)
        logger.exception(exc)

        request.response.status_int = 500

        return {
            "errors": [
                {
                    "status": request.response.status_int,
                    "code": "failed_to_get_transcript",
                    "title": "Failed to get transcript from YouTube",
                    "detail": str(exc).strip(),
                }
            ]
        }

    return {
        "data": {
            "type": "transcripts",
            "id": video_id,
            "attributes": {"segments": transcript},
        }
    }
