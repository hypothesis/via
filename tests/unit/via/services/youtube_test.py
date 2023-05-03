from unittest.mock import sentinel

import pytest

from via.services.youtube import YoutubeService, factory


class TestYoutubeService:
    @pytest.mark.parametrize(
        "url,video_id",
        [
            ("not_an_url", None),
            ("https://notyoutube:1000000", None),
            ("https://notyoutube.com", None),
            ("https://youtube.com", None),
            ("https://youtube.com?param=nope", None),
            ("https://youtube.com?v=", None),
            ("https://www.youtube.com/watch?v=VIDEO_ID", "VIDEO_ID"),
            ("https://www.youtube.com/watch?v=VIDEO_ID&t=14s", "VIDEO_ID"),
        ],
    )
    def test_parse_file_url(self, url, video_id):
        assert video_id == YoutubeService.parse_url(url)


def test_factory(pyramid_request):
    svc = factory(sentinel.context, pyramid_request)

    assert isinstance(svc, YoutubeService)
