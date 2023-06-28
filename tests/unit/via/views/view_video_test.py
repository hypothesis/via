from unittest.mock import sentinel

import pytest
from h_matchers import Any
from marshmallow.exceptions import ValidationError as MarshmallowValidationError
from pyramid.httpexceptions import HTTPUnauthorized

from via.exceptions import BadURL
from via.views.view_video import youtube

# webargs's kwargs injection into view functions falsely triggers Pylint's
# no-value-for-parameter all the time so just disable it file-wide.
# pylint: disable=no-value-for-parameter


@pytest.mark.usefixtures("youtube_service")
class TestViewVideo:
    def test_it(
        self,
        pyramid_request,
        Configuration,
        youtube_service,
        video_url,
        ViaSecurityPolicy,
    ):
        youtube_service.get_video_id.return_value = sentinel.youtube_video_id

        response = youtube(pyramid_request)

        youtube_service.get_video_id.assert_called_once_with(video_url)
        Configuration.extract_from_params.assert_called_once_with(
            {"via.foo": "foo", "via.bar": "bar"}
        )
        ViaSecurityPolicy.encode_jwt.assert_called_once_with(pyramid_request)
        assert response == {
            "client_embed_url": "http://hypothes.is/embed.js",
            "client_config": Configuration.extract_from_params.return_value[1],
            "video_id": sentinel.youtube_video_id,
            "api": {
                "transcript": {
                    "doc": Any.string(),
                    "url": pyramid_request.route_url(
                        "api.youtube.transcript", video_id=sentinel.youtube_video_id
                    ),
                    "method": "GET",
                    "headers": {
                        "Authorization": f"Bearer {ViaSecurityPolicy.encode_jwt.return_value}",
                    },
                }
            },
        }

    def test_it_errors_if_the_url_is_invalid(self, pyramid_request):
        pyramid_request.params["url"] = "not_a_valid_url"

        with pytest.raises(MarshmallowValidationError) as exc_info:
            youtube(pyramid_request)

        assert exc_info.value.normalized_messages() == {
            "query": {"url": ["Not a valid URL."]}
        }

    def test_it_errors_if_the_url_is_not_a_YouTube_url(
        self, pyramid_request, youtube_service
    ):
        # YouTubeService returns None if it can't extract the YouTube video ID
        # from the URL, which happens if the URL doesn't match a YouTube video
        # URL format that YouTubeService supports.
        youtube_service.get_video_id.return_value = None

        with pytest.raises(BadURL) as exc_info:
            youtube(pyramid_request)

        assert str(exc_info.value).startswith("Unsupported video URL")

    def test_it_with_YouTube_transcripts_disabled(
        self, pyramid_request, youtube_service
    ):
        youtube_service.enabled = False

        with pytest.raises(HTTPUnauthorized):
            youtube(pyramid_request)

    @pytest.fixture
    def video_url(self):
        return "https://example.com/watch?v=VIDEO_ID"

    @pytest.fixture
    def pyramid_request(self, pyramid_request, video_url):
        pyramid_request.params.update(
            {"url": video_url, "via.foo": "foo", "via.bar": "bar"}
        )
        return pyramid_request


@pytest.fixture(autouse=True)
def Configuration(patch):
    Configuration = patch("via.views.view_video.Configuration")
    Configuration.extract_from_params.return_value = (
        sentinel.via_config,
        sentinel.h_config,
    )
    return Configuration


@pytest.fixture(autouse=True)
def ViaSecurityPolicy(patch):
    return patch("via.views.view_video.ViaSecurityPolicy")
