from h_vialib import Configuration
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.view import view_config
from webargs import fields
from webargs.pyramidparser import use_kwargs

from via.exceptions import BadURL
from via.services import YouTubeService


@view_config(renderer="via:templates/view_video.html.jinja2", route_name="youtube")
@use_kwargs({"url": fields.Url(required=True)}, location="query")
def youtube(request, url):
    youtube_service = request.find_service(YouTubeService)

    if not youtube_service.enabled:
        raise HTTPUnauthorized()

    video_id = youtube_service.get_video_id(url)

    if not video_id:
        raise BadURL(f"Unsupported video URL: {url}", url=url)

    _, client_config = Configuration.extract_from_params(request.params)

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
