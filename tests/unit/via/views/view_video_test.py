from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPUnauthorized

from via.views.view_video import view_video


@pytest.mark.usefixtures("youtube_service")
class TestViewVideo:
    def test_it(self, pyramid_request, Configuration):
        pyramid_request.matchdict["id"] = "abcdef"

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
        assert response["video_id"] == "abcdef"

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
