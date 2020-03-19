from urllib.parse import urlparse

import mock
import pytest
from h_matchers import Any
from httpretty import httpretty
from requests import Response
from requests.exceptions import (
    MissingSchema,
    ProxyError,
    SSLError,
    UnrewindableBodyError,
)

from tests.unit.conftest import assert_cache_control
from via.exceptions import BadURL, UnhandledException, UpstreamServiceError
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
        self, content_type, location, call_route_by_content
    ):
        result = call_route_by_content(content_type)

        assert result.location == location

    def test_we_call_third_parties_correctly(self, call_route_by_content):
        call_route_by_content(
            target_url="http://example.com/path%2C?a=b", params={"other": "value"}
        )

        # The fact we got this far means we hit the right host as registered
        # with httpretty, so we just need to check the path. Which is just as
        # well, as httpretty doesn't appear to store the full URL

        assert (
            httpretty.last_request.path == "/path%2C?a=b"
        )  # pylint: disable=no-member

    def test_redirects_to_pdf_view_for_pdfs_have_the_correct_params(
        self, call_route_by_content
    ):
        url = "http://example.com/path%2C?a=b"
        results = call_route_by_content(
            "application/pdf", url, params={"other": "value"}
        )

        assert results.location == Any.url.with_query({"other": "value", "url": url})

    def test_requests_to_legacy_via_are_formatted_correctly(
        self, call_route_by_content
    ):
        path = "http://example.com/path%2C"
        url = path + "?a=b"
        results = call_route_by_content("text/html", url, params={"other": "value"})

        # This is horrible, but the params just get blended together. It's
        # via's job to separate them on the other side
        assert results.location == Any.url.with_path(path).with_query(
            {"a": "b", "other": "value"}
        )

    @pytest.mark.parametrize(
        "content_type,max_age", [("application/pdf", 300), ("text/html", 60)],
    )
    def test_sets_correct_cache_control(
        self, content_type, max_age, call_route_by_content
    ):
        result = call_route_by_content(content_type)

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
        self, status_code, cache, call_route_by_content, requests
    ):
        response = Response()
        response.status_code = status_code
        response.raw = mock.Mock()

        requests.get.return_value = response

        result = call_route_by_content("text/html")

        assert result.headers == Any.iterable.containing({"Cache-Control": cache})

    @pytest.mark.parametrize("bad_url", ("no-schema", "glub://example.com", "http://"))
    def test_it_raises_BadURL_for_invalid_urls(self, bad_url, call_route_by_content):
        with pytest.raises(BadURL):
            call_route_by_content(target_url=bad_url)

    @pytest.mark.parametrize(
        "request_exception,expected_exception",
        (
            (MissingSchema, BadURL),
            (ProxyError, UpstreamServiceError),
            (SSLError, UpstreamServiceError),
            (UnrewindableBodyError, UnhandledException),
        ),
    )
    def test_it_catches_requests_exceptions(
        self, requests, request_exception, expected_exception, call_route_by_content
    ):
        requests.get.side_effect = request_exception("Oh noe")

        with pytest.raises(expected_exception):
            call_route_by_content()

    @pytest.fixture
    def requests(self, patch):
        return patch("via.views.route_by_content.requests")

    @pytest.fixture
    def call_route_by_content(self, make_request):
        def call_route_by_content(
            content_type="text/html", target_url="http://example.com", params=None
        ):
            httpretty.register_uri(
                method=httpretty.GET,
                uri=urlparse(target_url)._replace(query=None, fragment=None).geturl(),
                body="DUMMY",
                adding_headers={"Content-Type": content_type},
            )

            return route_by_content(
                make_request(params=dict(params or {}, url=target_url))
            )

        return call_route_by_content
