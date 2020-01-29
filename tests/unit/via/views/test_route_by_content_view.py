from unittest import mock

import httpretty
import pytest
from h_matchers import Any
from requests import Response
from requests.exceptions import (
    MissingSchema,
    ProxyError,
    SSLError,
    UnrewindableBodyError,
)

from tests.unit.conftest import assert_cache_control
from via.exceptions import BadURL, UnhandledException, UpstreamServiceError
from via.views.route_by_content_view import route_by_content


class TestRouteByContent:
    @pytest.mark.parametrize(
        "requested_path,expected_location,content_type",
        [
            # If the requested pdf URL has no query string then it should just
            # redirect to the requested URL, with no query string (but with the
            (
                "/https://example.com/foo",
                "http://localhost/pdf/https://example.com/foo",
                "application/pdf",
            ),
            # If the requested pdf URL has a query string then the query string
            # should be preserved in the URL that it redirects to.
            (
                "/https://example.com/foo?bar=baz",
                "http://localhost/pdf/https://example.com/foo?bar=baz",
                "application/pdf",
            ),
            # If the requested html URL has a query string then the query string
            # should be preserved in the URL that it redirects to.
            (
                "/https://example.com/foo?bar=baz",
                "http://via.hypothes.is/https://example.com/foo?bar=baz",
                "text/html",
            ),
            # If the requested html URL has a client query params then the query params
            # should be preserved in the URL that it redirects to.
            (
                "/https://example.com/foo?via.open_sidebar=1",
                "http://via.hypothes.is/https://example.com/foo?via.open_sidebar=1",
                "text/html",
            ),
        ],
    )
    def test_redirect_location(
        self, make_pyramid_request, requested_path, expected_location, content_type
    ):

        request = make_pyramid_request(
            request_url=requested_path,
            thirdparty_url="https://example.com/foo",
            content_type=content_type,
        )

        redirect = route_by_content(request)

        assert redirect.location == expected_location

    @pytest.mark.parametrize(
        "content_type,redirect_url",
        [
            ("application/pdf", "http://localhost/pdf/https://example.com"),
            ("application/x-pdf", "http://localhost/pdf/https://example.com"),
            ("text/html", "http://via.hypothes.is/https://example.com"),
        ],
    )
    def test_redirects_based_on_content_type_header(
        self, make_pyramid_request, content_type, redirect_url
    ):
        request = make_pyramid_request(
            request_url="/https://example.com",
            thirdparty_url="https://example.com",
            content_type=content_type,
        )

        result = route_by_content(request)

        assert result.location == redirect_url

    @pytest.mark.parametrize(
        "query_param", ["via.request_config_from_frame", "via.open_sidebar"]
    )
    def test_does_not_pass_via_query_params_to_thirdparty_server(
        self, make_pyramid_request, query_param
    ):
        request = make_pyramid_request(
            request_url="/https://example.com?"
            "via.request_config_from_frame=lms.hypothes.is&via.open_sidebar=1",
            thirdparty_url="https://example.com",
            content_type="application/pdf",
        )

        route_by_content(request)

        # pylint: disable=no-member
        assert query_param not in httpretty.last_request().path

    @pytest.mark.parametrize(
        "content_type,max_age", [("application/pdf", 300), ("text/html", 60)],
    )
    def test_sets_correct_cache_control(
        self, content_type, max_age, make_pyramid_request
    ):
        request = make_pyramid_request(
            request_url="/http://example.com",
            thirdparty_url="http://example.com",
            content_type=content_type,
        )

        result = route_by_content(request)

        assert_cache_control(
            result.headers,
            ["public", f"max-age={max_age}", "stale-while-revalidate=86400"],
        )

    @pytest.mark.parametrize("bad_url", ("no-schema", "glub://example.com", "http://"))
    def test_invalid_urls_raise_BadURL(self, bad_url, make_pyramid_request):
        request = make_pyramid_request(
            request_url=f"/{bad_url}", thirdparty_url=bad_url, content_type="text/html",
        )

        with pytest.raises(BadURL):
            route_by_content(request)

    @pytest.mark.parametrize(
        "request_exception,expected_exception",
        (
            (MissingSchema, BadURL),
            (ProxyError, UpstreamServiceError),
            (SSLError, UpstreamServiceError),
            (UnrewindableBodyError, UnhandledException),
        ),
    )
    def test_we_catch_requests_exceptions(
        self, requests, request_exception, expected_exception, make_pyramid_request
    ):
        requests.get.side_effect = request_exception("Oh noe")

        request = make_pyramid_request(
            request_url="/http://example.com",
            thirdparty_url="http://example.com",
            content_type="text/html",
        )

        with pytest.raises(expected_exception):
            route_by_content(request)

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
        self, status_code, cache, make_pyramid_request, requests
    ):
        response = Response()
        response.status_code = status_code
        response.raw = mock.Mock()

        requests.get.return_value = response

        result = route_by_content(
            make_pyramid_request(
                request_url="/http://example.com",
                thirdparty_url="http://example.com",
                content_type="text/html",
            )
        )

        assert dict(result.headers) == Any.dict.containing({"Cache-Control": cache})

    @pytest.fixture
    def requests(self, patch):
        return patch("via.views.route_by_content_view.requests")

    @pytest.fixture
    def make_pyramid_request(self, make_pyramid_request):
        def _make_pyramid_request(request_url, thirdparty_url, content_type):
            httpretty.register_uri(
                httpretty.GET,
                thirdparty_url,
                body="{}",
                adding_headers={"Content-Type": content_type},
            )
            request = make_pyramid_request(request_url)
            request.matchdict = {"url": thirdparty_url}
            return request

        return _make_pyramid_request
