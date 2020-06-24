import pytest
from h_matchers import Any
from mock import sentinel
from webob.headers import EnvironHeaders

from tests.unit.conftest import assert_cache_control
from via.resources import URLResource
from via.views.route_by_content import route_by_content


class TestRouteByContent:
    @pytest.mark.parametrize(
        "content_type,location",
        (
            ("application/x-pdf", Any.url.with_path("/pdf")),
            ("application/pdf", Any.url.with_path("/pdf")),
            ("text/html", Any.url.with_host("via.hypothes.is")),
            ("other", Any.url.with_host("via.hypothes.is")),
        ),
    )
    def test_it_routes_by_content_type(
        self, content_type, location, call_route_by_content, get_url_details
    ):
        get_url_details.return_value = (content_type, 200)

        result = call_route_by_content()

        assert result.location == location

    def test_we_call_third_parties_correctly(
        self, call_route_by_content, get_url_details
    ):
        url = "http://example.com/path%2C?a=b"
        call_route_by_content(url, params={"other": "value"})

        get_url_details.assert_called_once_with(url, Any.instance_of(EnvironHeaders))

    @pytest.mark.usefixtures("pdf_response")
    def test_redirects_to_pdf_view_for_pdfs_have_the_correct_params(
        self, call_route_by_content
    ):
        url = "http://example.com/path%2C?a=b"
        results = call_route_by_content(url, params={"other": "value"})

        assert results.location == Any.url.with_query({"other": "value", "url": url})

    @pytest.mark.usefixtures("html_response")
    def test_requests_to_legacy_via_are_formatted_correctly(
        self, call_route_by_content
    ):
        path = "http://example.com/path%2C"
        url = path + "?a=b"
        results = call_route_by_content(url, params={"other": "value"})

        # This is horrible, but the params just get blended together. It's
        # via's job to separate them on the other side
        assert results.location == Any.url.with_path(path).with_query(
            {"a": "b", "other": "value"}
        )

    @pytest.mark.parametrize(
        "content_type,max_age", [("application/pdf", 300), ("text/html", 60)],
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

    @pytest.fixture(autouse=True)
    def get_url_details(self, patch):
        get_url_details = patch("via.views.route_by_content.get_url_details")
        get_url_details.return_value = (sentinel.content_type, 200)

        return get_url_details

    @pytest.fixture
    def pdf_response(self, get_url_details):
        get_url_details.return_value = ("application/pdf", 200)

    @pytest.fixture
    def html_response(self, get_url_details):
        get_url_details.return_value = ("application/html", 200)

    @pytest.fixture
    def call_route_by_content(self, make_request):
        def call_route_by_content(target_url="http://example.com", params=None):
            request = make_request(params=dict(params or {}, url=target_url))
            context = URLResource(request)

            return route_by_content(context, request)

        return call_route_by_content
