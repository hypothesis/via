import marshmallow
from h_vialib import Configuration
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.view import view_config
from webargs import fields
from webargs.pyramidparser import use_kwargs

from via.exceptions import BadURL
from via.security import ViaSecurityPolicy
from via.services import SecureLinkService, YouTubeService


def _is_lms_request(request):
    """Check if request comes from LMS (has a valid signed URL)."""
    return request.find_service(SecureLinkService).request_is_valid(request)


def _restricted_response(request, target_url=None):
    """Return the restricted access page response."""
    request.override_renderer = "via:templates/restricted.html.jinja2"
    return {"target_url": target_url}


def _api_headers(request):
    """Return common headers for API requests."""
    jwt = ViaSecurityPolicy.encode_jwt(request)
    return {"Authorization": f"Bearer {jwt}"}


@view_config(renderer="via:templates/view_video.html.jinja2", route_name="youtube")
@use_kwargs(
    {"url": fields.Url(required=True)}, location="query", unknown=marshmallow.INCLUDE
)
def youtube(request, url, **kwargs):
    """YouTube video viewer.

    If the request comes through LMS (valid signed URL), serve the viewer.
    Otherwise, show the restricted access page.
    """
    if not _is_lms_request(request):
        return _restricted_response(request, target_url=url)

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
    """HTML video viewer.

    If the request comes through LMS (valid signed URL), serve the viewer.
    Otherwise, show the restricted access page.
    """
    if not _is_lms_request(request):
        target_url = kwargs.get("url")
        return _restricted_response(request, target_url=target_url)

    allow_download = kwargs.get("allow_download", True)
    url = kwargs["url"]
    media_url = kwargs.get("media_url")
    transcript = kwargs["transcript"]

    video_title = kwargs.get("title") or "Video"
    media_url = media_url or url
    _, client_config = Configuration.extract_from_params(kwargs)

    return {
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
        "allow_download": allow_download,
        "video_src": media_url,
    }
