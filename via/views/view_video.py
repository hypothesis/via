import marshmallow
from h_matchers import Any
from h_vialib import Configuration
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.view import view_config
from webargs import fields
from webargs.pyramidparser import use_kwargs

from via.exceptions import BadURL
from via.security import ViaSecurityPolicy
from via.services import YouTubeService
from via.services.youtube_api import CaptionTrack

CAPTION_TRACK_PREFERENCES = (
    # Plain English first
    CaptionTrack(language_code="en"),
    # Plain varieties of English
    CaptionTrack(language_code=Any.string.matching("^en-.*")),
    # Sub-categories of plain English
    CaptionTrack(language_code="en", name=Any()),
    # English varieties with names
    CaptionTrack(language_code=Any.string.matching("^en-.*"), name=Any()),
    # Any auto generated English
    CaptionTrack(language_code=Any.string.matching("^en-.*"), name=Any(), kind=Any()),
    # Any track which can be translated into English
    CaptionTrack(
        language_code=Any(), name=Any(), kind=Any(), translated_language_code="en"
    ),
)


@view_config(renderer="via:templates/view_video.html.jinja2", route_name="youtube")
@use_kwargs(
    {"url": fields.Url(required=True)}, location="query", unknown=marshmallow.INCLUDE
)
def view_youtube_video(request, url, **kwargs):
    youtube_service: YouTubeService = request.find_service(YouTubeService)

    if not youtube_service.enabled:
        raise HTTPUnauthorized()

    video_id = youtube_service.get_video_id(url)
    if not video_id:
        raise BadURL(f"Unsupported video URL: {url}", url=url)

    video_url = youtube_service.canonical_video_url(video_id)
    video_title = youtube_service.get_video_title(video_id)

    via_config, client_config = Configuration.extract_from_params(kwargs)

    return {
        "client_embed_url": request.registry.settings["client_embed_url"],
        "client_config": client_config,
        "title": video_title,
        "video_id": video_id,
        "video_url": video_url,
        "api": {
            "transcript": {
                "doc": "Get the transcript of the current video",
                "url": request.route_url(
                    "api.youtube.transcript",
                    video_id=video_id,
                    transcript_id=_get_transcript_id(
                        youtube_service, video_url, via_config
                    ),
                ),
                "method": "GET",
                "headers": {
                    "Authorization": f"Bearer {ViaSecurityPolicy.encode_jwt(request)}"
                },
            }
        },
    }


def _get_transcript_id(youtube_service, url, via_config):
    # Try the `via.video.lang` param first
    if transcript_id := via_config.get("video", {}).get("lang"):
        return transcript_id

    # Then look up a transcript matching our preferences
    video = youtube_service.get_video_info(video_url=url)
    if video.has_captions and (
        caption_track := video.caption.find_matching_track(CAPTION_TRACK_PREFERENCES)
    ):
        return caption_track.id

    # This shouldn't be possible to get to if this was an option, but we need a
    # fall-back. We could also fail here instead?
    return "en.a"
