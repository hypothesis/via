from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPUnauthorized

from via.views.view_video import view_video


class TestViewVideo:
    def test_it(self, pyramid_request, Configuration, call_view, youtube_service):
        response = call_view(view=view_video, url="https://youtube.com")

        youtube_service.parse_url.assert_called_once_with("https://youtube.com")
        youtube_service.get_transcript.assert_called_once_with(
            youtube_service.parse_url.return_value
        )
        assert response["client_embed_url"] == "http://hypothes.is/embed.js"
        assert (
            response["client_config"]
            == Configuration.extract_from_params.return_value[1]
        )
        assert response["transcript"] == {
            "segments": youtube_service.get_transcript.return_value
        }
        assert response["video_id"] == youtube_service.parse_url.return_value

    def test_it_when_disabled(self, youtube_service, call_view):
        youtube_service.enabled = False

        response = call_view(view=view_video, url="https://youtube.com")

        assert isinstance(response, HTTPUnauthorized)

    @pytest.fixture
    def Configuration(self, patch):
        Configuration = patch("via.views.view_video.Configuration")
        Configuration.extract_from_params.return_value = (
            sentinel.via_config,
            sentinel.h_config,
        )

        return Configuration
