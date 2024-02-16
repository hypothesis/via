import marshmallow
from pyramid.view import view_config
from webargs import fields
from webargs.pyramidparser import use_kwargs

from via.services import TranscriptService


@view_config(
    route_name="api.video.transcript",
    request_method="GET",
    permission="api",
    renderer="json",
)
@use_kwargs(
    {"url": fields.Url(required=True)}, location="query", unknown=marshmallow.EXCLUDE
)
def get_transcript(request, url: str):
    """Fetch a video transcript.

    Fetches a transcript in WebVTT or SRT format and returns it as JSON.
    """

    transcript = request.find_service(TranscriptService).get_transcript(url)

    return {
        "data": {
            "type": "transcripts",
            "attributes": {"segments": transcript},
        }
    }
