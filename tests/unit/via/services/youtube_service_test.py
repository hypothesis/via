from unittest.mock import sentinel

import pytest

from via.services.youtube import YouTubeService, factory


class TestYouTubeService:
    @pytest.mark.parametrize("enabled", [True, False])
    def test_enabled(self, enabled):
        assert YouTubeService(enabled=enabled).enabled == enabled


class TestFactory:
    def test_it(self, YouTubeService, youtube_service, pyramid_request):
        returned = factory(sentinel.context, pyramid_request)

        YouTubeService.assert_called_once_with(
            pyramid_request.registry.settings["youtube_transcripts"]
        )
        assert returned == youtube_service

    @pytest.fixture(autouse=True)
    def YouTubeService(self, patch):
        return patch("via.services.youtube.YouTubeService")

    @pytest.fixture
    def youtube_service(self, YouTubeService):
        return YouTubeService.return_value
