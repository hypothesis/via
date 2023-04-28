from unittest.mock import sentinel

import pytest

from via.views.view_video import view_video


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

    @pytest.fixture
    def Configuration(self, patch):
        Configuration = patch("via.views.view_video.Configuration")
        Configuration.extract_from_params.return_value = (
            sentinel.via_config,
            sentinel.h_config,
        )

        return Configuration
