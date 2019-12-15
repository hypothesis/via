from unittest import mock

import httpretty
import pytest
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from py_proxy import views


class TestIndexRoute:
    def test_index_returns_empty_parameters_to_pass_to_template(self, pyramid_request):
        result = views.index(pyramid_request)

        assert result == {}

    def test_index_renders_input_for_entering_a_document_to_annotate(
        self, pyramid_request
    ):
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
    def test_status_returns_200_response(self, pyramid_request):
        result = views.status(pyramid_request)

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
    def test_returns_favicon_icon(self, pyramid_request):
        result = views.favicon(pyramid_request)

        assert result.content_type == "image/x-icon"
        assert result.status_int == 200


class TestRobotsTextRoute:
    def test_returns_robots_test_file(self, pyramid_request):
        result = views.robots(pyramid_request)

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
    def test_pdf_renders_parameters_in_pdf_template(
        self, pyramid_request, template_content
    ):
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

    def test_pdf_passes_thirdparty_url_to_renderer(self, pyramid_request, pdf_url):
        nginx_server = pyramid_request.registry.settings.get("nginx_server")
        result = views.pdf(pyramid_request)

        assert result["pdf_url"] == f"{nginx_server}/proxy/static/{pdf_url}"

    def test_pdf_passes_client_embed_url_to_renderer(self, pyramid_request):
        result = views.pdf(pyramid_request)

        assert (
            result["client_embed_url"]
            == pyramid_request.registry.settings["client_embed_url"]
        )

    @pytest.mark.parametrize(
        "h_open_sidebar,expected_h_open_sidebar", [("1", 1), ("0", 0), (None, 0)]
    )
    def test_pdf_passes_open_sidebar_query_parameter_to_renderer(
        self, pyramid_request, h_open_sidebar, expected_h_open_sidebar
    ):
        if h_open_sidebar is not None:
            pyramid_request.params["via.open_sidebar"] = h_open_sidebar
        result = views.pdf(pyramid_request)

        assert result["h_open_sidebar"] == expected_h_open_sidebar

    @pytest.mark.parametrize(
        "h_request_config,expected_h_request_config",
        [("http://lms.hypothes.is", "http://lms.hypothes.is"), (None, None)],
    )
    def test_pdf_passes_request_config_from_frame_query_parameter_to_renderer(
        self, pyramid_request, h_request_config, expected_h_request_config
    ):
        if h_request_config is not None:
            pyramid_request.params["via.request_config_from_frame"] = h_request_config

        result = views.pdf(pyramid_request)

        assert result["h_request_config"] == expected_h_request_config

    @pytest.fixture
    def pdf_url(self):
        return "http://thirdparty.url/foo.pdf"

    @pytest.fixture
    def pyramid_request(self, pyramid_request, pdf_url):
        pyramid_request.matchdict = {"pdf_url": pdf_url}
        return pyramid_request


class TestContentTypeRoute:
    @pytest.mark.parametrize(
        "content_type,redirect_location",
        [
            ("application/pdf", "/pdf/http://thirdparty.url"),
            ("application/x-pdf", "/pdf/http://thirdparty.url"),
            ("text/html", "http://via.hypothes.is/http://thirdparty.url"),
        ],
    )
    @httpretty.activate
    def test_redirects_based_on_content_type_header(
        self, pyramid_request, content_type, redirect_location
    ):
        httpretty.register_uri(
            httpretty.GET,
            "http://thirdparty.url",
            body="{}",
            adding_headers={"Content-Type": content_type},
        )

        result = views.content_type(pyramid_request)

        assert result.location == redirect_location

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict = {"url": "http://thirdparty.url"}

        def route_url(path, pdf_url):
            return f"/{path}/{pdf_url}"

        pyramid_request.route_url = route_url
        return pyramid_request
