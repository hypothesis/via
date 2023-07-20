from dataclasses import asdict

import marshmallow
from h_matchers import Any
from h_vialib import Configuration
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.view import view_config
from webargs import fields
from webargs.pyramidparser import use_kwargs

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

    via_config, client_config = Configuration.extract_from_params(kwargs)
    transcript_id = via_config.get("video", {}).get("lang")

    video = youtube_service.get_video_info(
        video_url=url, with_captions=not transcript_id
    )

    if not transcript_id:
        if caption_track := video.caption.find_matching_track(
            CAPTION_TRACK_PREFERENCES
        ):
            transcript_id = caption_track.id
        else:
            transcript_id = "en.a"

    return {
        "client_embed_url": request.registry.settings["client_embed_url"],
        "client_config": client_config,
        "video": asdict(video.details),
        "api": {
            "transcript": {
                "doc": "Get the transcript of the current video",
                "url": request.route_url(
                    "api.youtube.transcript",
                    video_id=video.details.id,
                    transcript_id=transcript_id,
                ),
                "method": "GET",
                "headers": {
                    "Authorization": f"Bearer {ViaSecurityPolicy.encode_jwt(request)}"
                },
            }
        },
    }
