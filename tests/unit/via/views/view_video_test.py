from unittest.mock import create_autospec

import pytest

from via.resources import QueryURLResource
from via.views.view_video import video, youtube


class TestYouTube:
    def test_it_returns_restricted_page_with_target_url(
        self, context, pyramid_request
    ):
        target = context.url_from_query.return_value = "https://youtube.com/watch?v=abc"

        result = youtube(context, pyramid_request)

        assert result == {"target_url": target}

    def test_it_returns_none_target_url_on_error(self, context, pyramid_request):
        context.url_from_query.side_effect = Exception("bad url")

        result = youtube(context, pyramid_request)

        assert result == {"target_url": None}

    @pytest.fixture
    def context(self):
        return create_autospec(QueryURLResource, spec_set=True, instance=True)


class TestVideo:
    def test_it_returns_restricted_page_with_target_url(self, pyramid_request):
        pyramid_request.params["url"] = "https://example.com/video.mp4"

        result = video(None, pyramid_request)

        assert result == {"target_url": "https://example.com/video.mp4"}

    def test_it_returns_none_target_url_when_no_url_param(self, pyramid_request):
        result = video(None, pyramid_request)

        assert result == {"target_url": None}
