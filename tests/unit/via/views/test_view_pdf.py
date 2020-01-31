import pytest
from markupsafe import Markup

from tests.unit.conftest import assert_cache_control
from via.views.view_pdf import view_pdf


class TestPdfRoute:
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

        final_pdf_url = view_pdf(request)["pdf_url"]

        assert final_pdf_url == f"{nginx_server}/proxy/static/{pdf_url}"

        # Check we disable Jinja 2 escaping
        assert isinstance(final_pdf_url, Markup)

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

        result = view_pdf(request)

        assert query_param not in result["pdf_url"]

    def test_pdf_passes_client_embed_url_to_renderer(self, make_pyramid_request):
        pdf_url = "https://example.com/foo.pdf"
        request = make_pyramid_request(f"/pdf/{pdf_url}", pdf_url)

        client_embed_url = view_pdf(request)["client_embed_url"]

        assert client_embed_url == request.registry.settings["client_embed_url"]

        # Check we disable Jinja 2 escaping
        assert isinstance(client_embed_url, Markup)

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

        result = view_pdf(request)

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
        result = view_pdf(request)

        assert result["h_request_config"] == expected_h_request_config

    def test_pdf_html_prevents_caching(self, test_app):
        response = test_app.get("/pdf/http://example.com/foo.pdf")

        assert_cache_control(
            response.headers, ["max-age=0", "must-revalidate", "no-cache", "no-store"]
        )

    @pytest.fixture
    def make_pyramid_request(self, make_pyramid_request):
        def _make_pyramid_request(request_url, thirdparty_url):
            request = make_pyramid_request(request_url)
            request.matchdict = {"pdf_url": thirdparty_url}
            return request

        return _make_pyramid_request
