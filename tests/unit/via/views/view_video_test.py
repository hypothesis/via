from unittest.mock import sentinel

import pytest
from h_matchers import Any
from marshmallow.exceptions import ValidationError as MarshmallowValidationError
from pyramid.httpexceptions import HTTPUnauthorized

from via.exceptions import BadURL
from via.views.view_video import video, youtube

# webargs's kwargs injection into view functions falsely triggers Pylint's
# no-value-for-parameter all the time so just disable it file-wide.
# pylint: disable=no-value-for-parameter


@pytest.mark.usefixtures("youtube_service")
class TestYouTube:
    def test_it(
        self,
        pyramid_request,
        Configuration,
        youtube_service,
        video_url,
        ViaSecurityPolicy,
    ):
        # Override default `None` response.
        youtube_service.get_video_id.return_value = sentinel.youtube_video_id

        response = youtube(pyramid_request)

        youtube_service.get_video_id.assert_called_once_with(video_url)
        youtube_service.canonical_video_url.assert_called_once_with(
            sentinel.youtube_video_id
        )
        youtube_service.get_video_title.assert_called_once_with(
            youtube_service.get_video_id.return_value
        )
        Configuration.extract_from_params.assert_called_once_with(
            {"via.foo": "foo", "via.bar": "bar"}
        )
        ViaSecurityPolicy.encode_jwt.assert_called_once_with(pyramid_request)
        assert response == {
            "client_embed_url": "http://hypothes.is/embed.js",
            "client_config": Configuration.extract_from_params.return_value[1],
            "player": "youtube",
            "title": youtube_service.get_video_title.return_value,
            "video_id": youtube_service.get_video_id.return_value,
            "video_url": youtube_service.canonical_video_url.return_value,
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


class TestVideo:
    def test_it(self, pyramid_request, Configuration, ViaSecurityPolicy):
        video_url = "https://example.com/video.mp4"
        transcript_url = "https://example.com/transcript.vtt"
        pyramid_request.params.update({"url": video_url, "transcript": transcript_url})

        response = video(pyramid_request)

        assert response == {
            "client_embed_url": "http://hypothes.is/embed.js",
            "client_config": Configuration.extract_from_params.return_value[1],
            "player": "html-video",
            "title": "Video",
            "video_url": "https://example.com/video.mp4",
            "api": {
                "transcript": {
                    "doc": Any.string(),
                    "url": pyramid_request.route_url(
                        "api.video.transcript", _query={"url": transcript_url}
                    ),
                    "method": "GET",
                    "headers": {
                        "Authorization": f"Bearer {ViaSecurityPolicy.encode_jwt.return_value}",
                    },
                },
            },
            # Fields specific to HTML video player.
            "video_src": video_url,
        }

    def test_it_sets_title(self, pyramid_request):
        video_url = "https://example.com/video.mp4"
        transcript_url = "https://example.com/transcript.vtt"
        pyramid_request.params.update(
            {"url": video_url, "transcript": transcript_url, "title": "Custom title"}
        )

        response = video(pyramid_request)

        assert response["title"] == "Custom title"

    def test_it_sets_video_src(self, pyramid_request):
        video_url = "https://example.com/video.mp4"
        transcript_url = "https://example.com/transcript.vtt"
        pyramid_request.params.update(
            {
                "url": video_url,
                "transcript": transcript_url,
                "media_url": "https://cdn.example.com/video.mp4?token=1234",
            }
        )

        response = video(pyramid_request)

        assert response["video_url"] == video_url
        assert response["video_src"] == "https://cdn.example.com/video.mp4?token=1234"


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
