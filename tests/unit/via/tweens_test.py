from unittest.mock import create_autospec

import pytest

from via.tweens import robots_tween_factory


class TestRobotsTween:
    @pytest.mark.parametrize(
        "existing_header,expected_header",
        [
            (None, "noindex, nofollow"),
            ("all", "all"),
        ],
    )
    def test_it(
        self, existing_header, expected_header, handler, pyramid_request, tween
    ):
        if existing_header:
            handler.return_value.headers = {"X-Robots-Tag": existing_header}
        else:
            handler.return_value.headers = {}

        response = tween(pyramid_request)

        handler.assert_called_once_with(pyramid_request)
        assert response == handler.return_value
        assert response.headers["X-Robots-Tag"] == expected_header

    @pytest.fixture
    def handler(self):
        def handler_spec(request):
            """Spec for mock handler function."""

        return create_autospec(handler_spec)

    @pytest.fixture
    def tween(self, handler, pyramid_request):
        return robots_tween_factory(handler, pyramid_request.registry)
