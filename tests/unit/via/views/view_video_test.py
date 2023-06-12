from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPUnauthorized

from via.exceptions import BadURL
from via.views.view_video import view_video


@pytest.mark.usefixtures("youtube_service")
class TestViewVideo:
    def test_it(self, pyramid_request, Configuration, youtube_service):
        youtube_service.get_video_id.return_value = sentinel.video_id

        response = view_video(pyramid_request)

        assert response["client_embed_url"] == "http://hypothes.is/embed.js"
        assert (
            response["client_config"]
            == Configuration.extract_from_params.return_value[1]
        )
        assert response["transcript"] == {
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
        assert response["video_id"] == sentinel.video_id

    def test_it_errors_if_the_url_is_invalid(self, pyramid_request, youtube_service):
        # YouTubeService returns None if it can't extract the YouTube video ID
        # from the URL, which happens if the URL doesn't match a YouTube video
        # URL format that YouTubeService supports.
        youtube_service.get_video_id.return_value = None

        with pytest.raises(BadURL) as exc_info:
            view_video(pyramid_request)

        assert str(exc_info.value).startswith("Unsupported video URL")

    def test_it_with_YouTube_transcripts_disabled(
        self, pyramid_request, youtube_service
    ):
        youtube_service.enabled = False

        with pytest.raises(HTTPUnauthorized):
            view_video(pyramid_request)

    @pytest.fixture
    def Configuration(self, patch):
        Configuration = patch("via.views.view_video.Configuration")
        Configuration.extract_from_params.return_value = (
            sentinel.via_config,
            sentinel.h_config,
        )

        return Configuration

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params["url"] = sentinel.url
        return pyramid_request
