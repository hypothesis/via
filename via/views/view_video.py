from h_vialib import Configuration
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.view import view_config

from via.services import YoutubeService


@view_config(
    renderer="via:templates/video_player.html.jinja2",
    route_name="view_video",
)
def view_video(context, request):
    _, h_config = Configuration.extract_from_params(request.params)
    youtube_service = request.find_service(YoutubeService)

    if not youtube_service.enabled:
        return HTTPUnauthorized()

    video_id = youtube_service.parse_url(context.url_from_query())
    request.checkmate.raise_if_blocked(context.url_from_query())

    return {
        "client_embed_url": request.registry.settings["client_embed_url"],
        "client_config": h_config,
        "transcript": {"segments": youtube_service.get_transcript(video_id)},
        "video_id": video_id,
    }
