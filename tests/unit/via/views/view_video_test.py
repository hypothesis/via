from unittest.mock import sentinel

import pytest
from h_matchers import Any
from marshmallow.exceptions import ValidationError as MarshmallowValidationError
from pyramid.httpexceptions import HTTPUnauthorized

from via.exceptions import BadURL
from via.views.view_video import CAPTION_TRACK_PREFERENCES, view_youtube_video

# webargs's kwargs injection into view functions falsely triggers Pylint's
# no-value-for-parameter all the time so just disable it file-wide.
# pylint: disable=no-value-for-parameter


@pytest.mark.usefixtures("youtube_service")
class TestViewVideo:
    def test_it(
        self,
        pyramid_request,
        youtube_service,
        video_url,
        ViaSecurityPolicy,
    ):
        pyramid_request.params["via.video.lang"] = sentinel.transcript_id

        response = view_youtube_video(pyramid_request)

        youtube_service.get_video_id.assert_called_once_with(video_url)
        video_id = youtube_service.get_video_id.return_value
        youtube_service.canonical_video_url.assert_called_once_with(video_id)
        youtube_service.get_video_title.assert_called_once_with(
            youtube_service.get_video_id.return_value
        )

        ViaSecurityPolicy.encode_jwt.assert_called_once_with(pyramid_request)
        assert response == {
            "client_embed_url": "http://hypothes.is/embed.js",
            "client_config": {
                "appType": "via",
                "openSidebar": False,
                "showHighlights": True,
            },
            "title": youtube_service.get_video_title.return_value,
            "video_id": video_id,
            "video_url": youtube_service.canonical_video_url.return_value,
            "api": {
                "transcript": {
                    "doc": Any.string(),
                    "url": pyramid_request.route_url(
                        "api.youtube.transcript",
                        video_id=video_id,
                        transcript_id=sentinel.transcript_id,
                    ),
                    "method": "GET",
                    "headers": {
                        "Authorization": f"Bearer {ViaSecurityPolicy.encode_jwt.return_value}",
                    },
                }
            },
        }

    def test_it_looks_up_transcripts(self, pyramid_request, youtube_service):
        pyramid_request.params.pop("via.video.lang", None)

        response = view_youtube_video(pyramid_request)

        youtube_service.get_video_info.assert_called_once_with(
            video_url=youtube_service.canonical_video_url.return_value
        )
        video = youtube_service.get_video_info.return_value
        video.caption.find_matching_track.assert_called_once_with(
            CAPTION_TRACK_PREFERENCES
        )
        caption_track = video.caption.find_matching_track.return_value

        assert response["api"]["transcript"]["url"] == pyramid_request.route_url(
            "api.youtube.transcript",
            video_id=youtube_service.get_video_id.return_value,
            transcript_id=caption_track.id,
        )

    @pytest.mark.parametrize("has_captions,has_matches", ((True, False), (False, True)))
    def test_it_defaults_to_en_a(
        self, pyramid_request, youtube_service, has_captions, has_matches
    ):
        pyramid_request.params.pop("via.video.lang", None)
        video = youtube_service.get_video_info.return_value
        video.has_captions = has_captions
        if not has_matches:
            video.caption.find_matching_track.return_value = None

        response = view_youtube_video(pyramid_request)

        assert response["api"]["transcript"]["url"] == pyramid_request.route_url(
            "api.youtube.transcript",
            video_id=youtube_service.get_video_id.return_value,
            transcript_id="en.a",
        )

    def test_it_errors_if_the_url_is_invalid(self, pyramid_request):
        pyramid_request.params["url"] = "not_a_valid_url"

        with pytest.raises(MarshmallowValidationError) as exc_info:
            view_youtube_video(pyramid_request)

        assert exc_info.value.normalized_messages() == {
            "query": {"url": ["Not a valid URL."]}
        }

    def test_it_errors_if_the_url_is_not_a_youtube_url(
        self, pyramid_request, youtube_service
    ):
        # YouTubeService returns None if it can't extract the YouTube video ID
        # from the URL, which happens if the URL doesn't match a YouTube video
        # URL format that YouTubeService supports.
        youtube_service.get_video_id.return_value = None

        with pytest.raises(BadURL) as exc_info:
            view_youtube_video(pyramid_request)

        assert str(exc_info.value).startswith("Unsupported video URL")

    def test_it_with_YouTube_transcripts_disabled(
        self, pyramid_request, youtube_service
    ):
        youtube_service.enabled = False

        with pytest.raises(HTTPUnauthorized):
            view_youtube_video(pyramid_request)

    @pytest.fixture
    def video_url(self):
        return "https://example.com/watch?v=VIDEO_ID"

    @pytest.fixture
    def pyramid_request(self, pyramid_request, video_url):
        pyramid_request.params["url"] = video_url

        return pyramid_request

    @pytest.fixture(autouse=True)
    def ViaSecurityPolicy(self, patch):
        return patch("via.views.view_video.ViaSecurityPolicy")
