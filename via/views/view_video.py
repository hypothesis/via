import marshmallow
from h_vialib import Configuration
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.view import view_config
from webargs import fields
from webargs.pyramidparser import use_kwargs

from via.exceptions import BadURL
from via.security import ViaSecurityPolicy
from via.services import YouTubeService


def _api_headers(request):
    """Return common headers for API requests."""
    jwt = ViaSecurityPolicy.encode_jwt(request)
    return {"Authorization": f"Bearer {jwt}"}


@view_config(renderer="via:templates/view_video.html.jinja2", route_name="youtube")
@use_kwargs(
    {"url": fields.Url(required=True)}, location="query", unknown=marshmallow.INCLUDE
)
def youtube(request, url, **kwargs):
    youtube_service = request.find_service(YouTubeService)

    if not youtube_service.enabled:
        raise HTTPUnauthorized()  # noqa: RSE102

    video_id = youtube_service.get_video_id(url)
    video_url = youtube_service.canonical_video_url(video_id)
    video_title = youtube_service.get_video_title(video_id)

    if not video_id:
        raise BadURL(f"Unsupported video URL: {url}", url=url)  # noqa: EM102, TRY003

    _, client_config = Configuration.extract_from_params(kwargs)

    return {
        # Common video player fields
        "client_embed_url": request.registry.settings["client_embed_url"],
        "client_config": client_config,
        "player": "youtube",
        "title": video_title,
        "video_url": video_url,
        "api": {
            "transcript": {
                "doc": "Get the transcript of the current video",
                "url": request.route_url("api.youtube.transcript", video_id=video_id),
                "method": "GET",
                "headers": _api_headers(request),
            }
        },
        # Fields specific to YouTube video player
        "video_id": video_id,
    }


@view_config(
    route_name="video",
    renderer="via:templates/view_video.html.jinja2",
)
@use_kwargs(
    {
        "url": fields.Url(required=True),
        "media_url": fields.Url(required=False),
        "transcript": fields.Url(required=True),
        "title": fields.Str(required=False),
        "allow_download": fields.Boolean(required=False),
    },
    location="query",
    unknown=marshmallow.INCLUDE,
)
def video(request, **kwargs):
    allow_download = kwargs.get("allow_download", True)
    url = kwargs["url"]
    media_url = kwargs.get("media_url")
    transcript = kwargs["transcript"]

    video_title = kwargs.get("title") or "Video"
    media_url = media_url or url
    _, client_config = Configuration.extract_from_params(kwargs)

    return {
        # Common video player fields
        "client_embed_url": request.registry.settings["client_embed_url"],
        "client_config": client_config,
        "player": "html-video",
        "title": video_title,
        "video_url": url,
        "api": {
            "transcript": {
                "doc": "Get the transcript of the current video",
                "url": request.route_url(
                    "api.video.transcript", _query={"url": transcript}
                ),
                "method": "GET",
                "headers": _api_headers(request),
            },
        },
        # Fields specific to HTML video player.
        "allow_download": allow_download,
        "video_src": media_url,
    }
