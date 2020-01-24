from unittest import mock

import httpretty
import pytest
from bs4 import BeautifulSoup
from h_matchers import Any
from jinja2 import Environment, FileSystemLoader
from pkg_resources import resource_filename
from requests import Response

from py_proxy import views

# pylint: disable=no-value-for-parameter
# Pylint doesn't seem to understand h_matchers here for some reason


def assert_cache_control(headers, max_age, stale_while_revalidate):

    assert dict(headers) == Any.dict.containing({"Cache-Control": Any.string()})

    header = headers["Cache-Control"]
    parts = sorted(header.split(", "))

    assert "public" in parts
    assert f"max-age={max_age}" in parts
    assert f"stale-while-revalidate={stale_while_revalidate}" in parts


class TestStatusRoute:
    def test_status_returns_200_response(self, make_pyramid_request):
        request = make_pyramid_request("/status")

        result = views.status(request)

        assert result.status == "200 OK"
        assert result.status_int == 200


class TestIncludeMe:
    config = mock.MagicMock()

    views.includeme(config)

    assert config.add_route.call_args_list == [
        mock.call("status", "/_status"),
        mock.call("pdf", "/pdf/{pdf_url:.*}"),
        mock.call("content_type", "/{url:.*}"),
    ]
    config.scan.assert_called_once_with("py_proxy.views")


class TestPdfRoute:
    @pytest.mark.parametrize(
        "template_content",
        [
            'window.PDF_URL = "https://via3.hypothes.is/proxy/static/http://example.com";',
            'window.CLIENT_EMBED_URL = "https://hypothes.is/embed.js";',
            "openSidebar: true",
            "requestConfigFromFrame: 'https://lms.hypothes.is'",
        ],
        ids=[
            "sets PDF_URL to proxied pdf url",
            "sets CLIENT_EMBED_URL to client embed url",
            "configures open_sidebar client setting",
            "configures open_sidebar client setting",
        ],
    )
    def test_pdf_renders_parameters_in_pdf_template(
        self, template_content, template_env
    ):
        template = template_env.get_template("pdfjs_viewer.html.jinja2")
        html = template.render(
            {
                "pdf_url": "https://via3.hypothes.is/proxy/static/http://example.com",
                "client_embed_url": "https://hypothes.is/embed.js",
                "h_open_sidebar": True,
                "h_request_config": "https://lms.hypothes.is",
            }
        )
        tree = BeautifulSoup(html, features="html.parser")

        assert template_content in str(tree.head)

    @pytest.mark.parametrize(
        "pdf_url",
        [
            "http://example.com/foo.pdf",
            "http://example.com/foo.pdf?param1=abc&param2=123",
        ],
    )
    def test_pdf_passes_thirdparty_url_to_renderer(self, make_pyramid_request, pdf_url):
        request = make_pyramid_request(f"/pdf/{pdf_url}", "http://example.com/foo.pdf")
        nginx_server = request.registry.settings.get("nginx_server")

        result = views.pdf(request)

        assert result["pdf_url"] == f"{nginx_server}/proxy/static/{pdf_url}"

    @pytest.mark.parametrize(
        "query_param", ["via.request_config_from_frame", "via.open_sidebar"]
    )
    def test_does_not_include_via_query_params_in_pdf_url(
        self, make_pyramid_request, query_param
    ):
        url = (
            "http://example.com/foo.pdf?param1=abc&param2=123"
            "&via.request_config_from_frame=lms.hypothes.is&via.open_sidebar=1"
        )

        request = make_pyramid_request(f"/pdf/{url}", "http://example.com/foo.pdf")

        result = views.pdf(request)

        assert query_param not in result["pdf_url"]

    def test_pdf_passes_client_embed_url_to_renderer(self, make_pyramid_request):
        pdf_url = "https://example.com/foo.pdf"
        request = make_pyramid_request(f"/pdf/{pdf_url}", pdf_url)

        result = views.pdf(request)

        assert (
            result["client_embed_url"] == request.registry.settings["client_embed_url"]
        )

    @pytest.mark.parametrize(
        "request_url,expected_h_open_sidebar",
        [
            ("/pdf/https://example.com/foo.pdf?via.open_sidebar=1", True),
            ("/pdf/https://example.com/foo.pdf?via.open_sidebar=foo", False),
            ("/pdf/https://example.com/foo.pdf?via.open_sidebar=0", False),
            ("/pdf/https://example.com/foo.pdf", False),
        ],
    )
    def test_pdf_passes_open_sidebar_query_parameter_to_renderer(
        self, make_pyramid_request, request_url, expected_h_open_sidebar
    ):
        request = make_pyramid_request(request_url, "http://example.com/foo.pdf")

        result = views.pdf(request)

        assert result["h_open_sidebar"] == expected_h_open_sidebar

    @pytest.mark.parametrize(
        "request_url,expected_h_request_config",
        [
            (
                "/pdf/http://example.com/foo.pdf?"
                "via.request_config_from_frame=http://lms.hypothes.is",
                "http://lms.hypothes.is",
            ),
            ("/pdf/http://example.com/foo.pdf", None),
        ],
    )
    def test_pdf_passes_request_config_from_frame_query_parameter_to_renderer(
        self, make_pyramid_request, request_url, expected_h_request_config
    ):
        request = make_pyramid_request(request_url, "http://example.com/foo.pdf")
        result = views.pdf(request)

        assert result["h_request_config"] == expected_h_request_config

    def test_pdf_adds_caching_headers(self, test_app):
        response = test_app.get("/pdf/http://example.com/foo.pdf")

        assert_cache_control(
            response.headers, max_age=86400, stale_while_revalidate=86400
        )

    @pytest.fixture
    def make_pyramid_request(self, make_pyramid_request):
        def _make_pyramid_request(request_url, thirdparty_url):
            request = make_pyramid_request(request_url)
            request.matchdict = {"pdf_url": thirdparty_url}
            return request

        return _make_pyramid_request


class TestContentTypeRoute:
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

        redirect = views.content_type(request)

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

        result = views.content_type(request)

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

        views.content_type(request)

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

        result = views.content_type(request)

        assert_cache_control(
            result.headers, max_age=max_age, stale_while_revalidate=86400
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
        self, status_code, cache, make_pyramid_request, requests
    ):
        response = Response()
        response.status_code = status_code
        response.raw = mock.Mock()

        requests.get.return_value = response

        result = views.content_type(
            make_pyramid_request(
                request_url="/http://example.com",
                thirdparty_url="http://example.com",
                content_type="text/html",
            )
        )

        assert dict(result.headers) == Any.dict.containing({"Cache-Control": cache})

    @pytest.fixture
    def requests(self, patch):
        return patch("py_proxy.views.requests")

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


@pytest.fixture
def template_env():
    return Environment(
        loader=FileSystemLoader(resource_filename("py_proxy", "templates"))
    )
