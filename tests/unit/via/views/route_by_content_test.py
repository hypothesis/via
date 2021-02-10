from unittest.mock import sentinel

import pytest
from h_matchers import Any
from webob.headers import EnvironHeaders

from tests.conftest import assert_cache_control
from via.resources import URLResource
from via.views.route_by_content import route_by_content


@pytest.mark.usefixtures("via_client_service")
class TestRouteByContent:
    @pytest.mark.parametrize(
        "content_type,passed_type",
        (
            ("application/x-pdf", "pdf"),
            ("application/pdf", "pdf"),
            ("text/html", "html"),
            ("other", "html"),
        ),
    )
    def test_it_routes_by_content_type(
        self,
        content_type,
        passed_type,
        call_route_by_content,
        get_url_details,
        via_client_service,
    ):
        url = "http://example.com/path%2C?a=b"
        get_url_details.return_value = (content_type, 200)

        results = call_route_by_content(url, params={"other": "value"})

        via_client_service.url_for.assert_called_once_with(
            url, content_type=passed_type, options={"other": "value"}
        )

        assert results.location == via_client_service.url_for.return_value

    def test_we_call_third_parties_correctly(
        self, call_route_by_content, get_url_details
    ):
        url = "http://example.com/path%2C?a=b"
        call_route_by_content(url, params={"other": "value"})

        get_url_details.assert_called_once_with(url, Any.instance_of(EnvironHeaders))

    @pytest.mark.parametrize(
        "content_type,max_age", [("application/pdf", 300), ("text/html", 60)]
    )
    def test_sets_correct_cache_control(
        self, content_type, max_age, call_route_by_content, get_url_details
    ):
        get_url_details.return_value = (content_type, 200)

        result = call_route_by_content()

        assert_cache_control(
            result.headers,
            ["public", f"max-age={max_age}", "stale-while-revalidate=86400"],
        )

    @pytest.mark.parametrize(
        "status_code,cache",
        (
            (200, Any.string.containing("max-age=60")),
            (401, Any.string.containing("max-age=60")),
            (404, Any.string.containing("max-age=60")),
            (500, "no-cache"),
            (501, "no-cache"),
        ),
    )
    def test_cache_http_response_codes_appropriately(
        self, status_code, cache, call_route_by_content, get_url_details
    ):
        get_url_details.return_value = (sentinel.content_type, status_code)

        result = call_route_by_content()

        assert result.headers == Any.iterable.containing({"Cache-Control": cache})

    @pytest.fixture
    def call_route_by_content(self, make_request):
        def call_route_by_content(target_url="http://example.com", params=None):
            request = make_request(params=dict(params or {}, url=target_url))
            context = URLResource(request)

            return route_by_content(context, request)

        return call_route_by_content

    @pytest.fixture(autouse=True)
    def get_url_details(self, patch):
        get_url_details = patch("via.views.route_by_content.get_url_details")
        get_url_details.return_value = (sentinel.content_type, 200)

        return get_url_details
