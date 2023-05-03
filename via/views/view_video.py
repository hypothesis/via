from h_vialib import Configuration
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.view import view_config

from via.services import YoutubeService


@view_config(renderer="via:templates/view_video.html.jinja2", route_name="view_video")
def view_video(context, request):
    _, client_config = Configuration.extract_from_params(request.params)
    youtube_service = request.find_service(YoutubeService)

    if not youtube_service.enabled:
        return HTTPUnauthorized()

    video_id = youtube_service.parse_url(context.url_from_query())
    request.checkmate.raise_if_blocked(context.url_from_query())

    transcript = {
        "segments": [
            {
                "time": 0,
                "text": "First segment of transcript",
            },
            {
                "time": 30,
                "text": "Second segment of transcript",
            },
        ],
    }

    return {
        "client_embed_url": request.registry.settings["client_embed_url"],
        "client_config": client_config,
        "transcript": transcript,
        "video_id": video_id,
    }
