from unittest import mock

import httpretty
import pytest
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from py_proxy import views


class TestIndexRoute:
    def test_index_returns_empty_parameters_to_pass_to_template(
        self, make_pyramid_request
    ):
        request = make_pyramid_request("/status")

        result = views.index(request)

        assert result == {}

    def test_index_renders_input_for_entering_a_document_to_annotate(self,):
        env = Environment(loader=FileSystemLoader("."))

        template = env.get_template("py_proxy/templates/index.html.jinja2")
        html = template.render({})
        tree = BeautifulSoup(html, features="html.parser")

        expected = (
            '<input aria-label="Web or PDF document to annotate" '
            'autofocus="" class="url-field" id="search" name="search" '
            'placeholder="Paste a link to annotate" type="url"/>'
        )
        assert str(tree.body.form.input) == expected


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
        mock.call("index", "/"),
        mock.call("status", "/_status"),
        mock.call("favicon", "/favicon.ico"),
        mock.call("robots", "/robots.txt"),
        mock.call("pdf", "/pdf/{pdf_url:.*}"),
        mock.call("content_type", "/{url:.*}"),
    ]
    config.scan.assert_called_once_with("py_proxy.views")


class TestFaviconRoute:
    def test_returns_favicon_icon(self, make_pyramid_request):
        request = make_pyramid_request("/favicon.ico")

        result = views.favicon(request)

        assert result.content_type == "image/x-icon"
        assert result.status_int == 200


class TestRobotsTextRoute:
    def test_returns_robots_test_file(self, make_pyramid_request):
        request = make_pyramid_request("/robots.txt")

        result = views.robots(request)

        assert result.content_type == "text/plain"
        assert result.status_int == 200


class TestPdfRoute:
    @pytest.mark.parametrize(
        "template_content",
        [
            'window.PDF_URL = "https://via3.hypothes.is/proxy/static/http://thirdparty.url";',
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
    def test_pdf_renders_parameters_in_pdf_template(self, template_content):
        env = Environment(loader=FileSystemLoader("."))

        template = env.get_template("py_proxy/templates/pdfjs_viewer.html.jinja2")
        html = template.render(
            {
                "pdf_url": "https://via3.hypothes.is/proxy/static/http://thirdparty.url",
                "client_embed_url": "https://hypothes.is/embed.js",
                "h_open_sidebar": 1,
                "h_request_config": "https://lms.hypothes.is",
            }
        )
        tree = BeautifulSoup(html, features="html.parser")

        assert template_content in str(tree.head)

    @pytest.mark.parametrize(
        "pdf_url",
        [
            "http://thirdparty.url/foo.pdf",
            "http://thirdparty.url/foo.pdf?param1=abc&param2=123",
        ],
    )
    def test_pdf_passes_thirdparty_url_to_renderer(self, make_pyramid_request, pdf_url):
        request = make_pyramid_request(f"/pdf/{pdf_url}")
        nginx_server = request.registry.settings.get("nginx_server")

        result = views.pdf(request)

        assert result["pdf_url"] == f"{nginx_server}/proxy/static/{pdf_url}"

    @pytest.mark.parametrize(
        "query_param", ["via.request_config_from_frame", "via.open_sidebar"]
    )
    @pytest.mark.xfail(raises=AssertionError)
    @httpretty.activate
    def test_does_not_include_via_query_params_in_pdf_url(
        self, make_pyramid_request, query_param
    ):
        url = (
            "http://thirdparty.url/foo.pdf?param1=abc&param2=123"
            "via.request_config_from_frame=lms.hypothes.is&via.open_sidebar=1"
        )

        request = make_pyramid_request(f"/pdf/{url}")

        result = views.pdf(request)

        assert query_param not in result["pdf_url"]

    def test_pdf_passes_client_embed_url_to_renderer(self, make_pyramid_request):
        request = make_pyramid_request("/pdf/https://thirdparty.url/foo.pdf")

        result = views.pdf(request)

        assert (
            result["client_embed_url"] == request.registry.settings["client_embed_url"]
        )

    @pytest.mark.parametrize(
        "request_url,expected_h_open_sidebar",
        [
            ("/pdf/https://thirdparty.url/foo.pdf?via.open_sidebar=1", 1),
            ("/pdf/https://thirdparty.url/foo.pdf?via.open_sidebar=0", 0),
            ("/pdf/https://thirdparty.url/foo.pdf", 0),
        ],
    )
    def test_pdf_passes_open_sidebar_query_parameter_to_renderer(
        self, make_pyramid_request, request_url, expected_h_open_sidebar
    ):
        request = make_pyramid_request(request_url)

        result = views.pdf(request)

        assert result["h_open_sidebar"] == expected_h_open_sidebar

    @pytest.mark.parametrize(
        "request_url,expected_h_request_config",
        [
            (
                "/pdf/http://thirdparty.url/foo.pdf?"
                "via.request_config_from_frame=http://lms.hypothes.is",
                "http://lms.hypothes.is",
            ),
            ("/pdf/http://thirdparty.url/foo.pdf", None),
        ],
    )
    def test_pdf_passes_request_config_from_frame_query_parameter_to_renderer(
        self, make_pyramid_request, request_url, expected_h_request_config
    ):
        request = make_pyramid_request(request_url)

        result = views.pdf(request)

        assert result["h_request_config"] == expected_h_request_config


class TestContentTypeRoute:
    @pytest.mark.parametrize(
        "requested_path,expected_location,content_type",
        [
            # If the requested pdf URL has no query string then it should just
            # redirect to the requested URL, with no query string (but with the
            (
                "/https://thirdparty.url/foo.pdf",
                "http://localhost/pdf/https://thirdparty.url/foo.pdf",
                "application/pdf",
            ),
            # If the requested pdf URL has a query string then the query string
            # should be preserved in the URL that it redirects to.
            (
                "/https://thirdparty.url/foo.pdf?bar=baz",
                "http://localhost/pdf/https://thirdparty.url/foo.pdf?bar=baz",
                "application/pdf",
            ),
            # If the requested html URL has a query string then the query string
            # should be preserved in the URL that it redirects to.
            (
                "/https://thirdparty.url/foo.pdf?bar=baz",
                "http://via.hypothes.is/https://thirdparty.url/foo.pdf?bar=baz",
                "text/html",
            ),
        ],
    )
    def test_redirect_location(
        self, make_pyramid_request, requested_path, expected_location, content_type
    ):

        request = make_pyramid_request(
            request_url=requested_path,
            thirdparty_url="https://thirdparty.url/foo.pdf",
            content_type=content_type,
        )

        redirect = views.content_type(request)

        assert redirect.location == expected_location

    @pytest.mark.parametrize(
        "content_type,redirect_url",
        [
            ("application/pdf", "http://localhost/pdf/https://thirdparty.url"),
            ("application/x-pdf", "http://localhost/pdf/https://thirdparty.url"),
            ("text/html", "http://via.hypothes.is/https://thirdparty.url"),
        ],
    )
    def test_redirects_based_on_content_type_header(
        self, make_pyramid_request, content_type, redirect_url
    ):
        request = make_pyramid_request(
            request_url="/https://thirdparty.url",
            thirdparty_url="https://thirdparty.url",
            content_type=content_type,
        )

        result = views.content_type(request)

        assert result.location == redirect_url

    @pytest.mark.parametrize(
        "query_param", ["via.request_config_from_frame", "via.open_sidebar"]
    )
    @pytest.mark.xfail(raises=AssertionError)
    def test_does_not_pass_via_query_params_to_thirdparty_server(
        self, make_pyramid_request, query_param
    ):
        request = make_pyramid_request(
            request_url="/https://thirdparty.url?"
            "via.request_config_from_frame=lms.hypothes.is&via.open_sidebar=1",
            thirdparty_url="https://thirdparty.url",
            content_type="application/pdf",
        )

        views.content_type(request)

        # pylint: disable=no-member
        assert query_param not in httpretty.last_request().path

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
