import marshmallow
from h_vialib import Configuration
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.view import view_config
from webargs import fields
from webargs.pyramidparser import use_kwargs

from via.security import ViaSecurityPolicy
from via.services import YouTubeService


@view_config(renderer="via:templates/view_video.html.jinja2", route_name="youtube")
@use_kwargs(
    {"url": fields.Url(required=True)}, location="query", unknown=marshmallow.INCLUDE
)
def youtube(request, url, **kwargs):
    youtube_service: YouTubeService = request.find_service(YouTubeService)

    if not youtube_service.enabled:
        raise HTTPUnauthorized()

    video = youtube_service.get_video_info(video_url=url)

    # This isn't how you'd want to do it in the end, but for now this implements
    # picking the first English subtitle we spot. This makes the transcript URL
    # completely deterministic. We could instead let that choose

    caption_track_id = ".en"
    if video.has_captions:
        for caption_track in video.caption.tracks:
            if caption_track.language_code == "en":
                print("Choosing", caption_track.name)
                caption_track_id = caption_track.id

    _, client_config = Configuration.extract_from_params(kwargs)

    return {
        "client_embed_url": request.registry.settings["client_embed_url"],
        "client_config": client_config,
        "video": {
            "id": video.details.id,
            "url": video.url,
            "title": video.details.title,
        },
        "api": {
            "transcript": {
                "doc": "Get the transcript of the current video",
                "url": request.route_url("api.youtube.transcript", video_id=video.id, caption_track_id=caption_track_id),
                "method": "GET",
                "headers": {
                    "Authorization": f"Bearer {ViaSecurityPolicy.encode_jwt(request)}"
                },
            }
        },
    }
