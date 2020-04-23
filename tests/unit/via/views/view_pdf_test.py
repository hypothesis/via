import pytest
from h_matchers import Any
from markupsafe import Markup

from tests.unit.conftest import assert_cache_control
from via.resources import URLResource
from via.views.view_pdf import view_pdf


class TestViewPDF:
    def test_it_passes_through_static_config(self, call_view_pdf, pyramid_settings):
        response = call_view_pdf()

        assert response == Any.dict.containing(
            {
                "client_embed_url": pyramid_settings["client_embed_url"],
                "static_url": Any.function(),
            }
        )

        # Check we disable Jinja 2 escaping
        assert isinstance(response["client_embed_url"], Markup)

    @pytest.mark.parametrize(
        "pdf_url",
        [
            "http://example.com/foo.pdf",
            "http://example.com/foo.pdf?a=1&a=2",
            "http://example.com/foo%2C.pdf?a=1&a=2",
        ],
    )
    def test_we_pass_through_the_url_exactly(
        self, call_view_pdf, pdf_url, pyramid_settings
    ):
        response = call_view_pdf(pdf_url)

        assert (
            response["pdf_url"]
            == f"{pyramid_settings['nginx_server']}/proxy/static/{pdf_url}"
        )

        # Check we disable Jinja 2 escaping
        assert isinstance(response["pdf_url"], Markup)

    def test_caching_is_disabled(self, test_app):
        response = test_app.get("/pdf?url=http://example.com/foo.pdf")

        assert_cache_control(
            response.headers, ["max-age=0", "must-revalidate", "no-cache", "no-store"]
        )


class TestHypothesisConfigConstruction:
    MISSING = object()

    def test_it_sets_expected_defaults(self, call_view_pdf):
        response = call_view_pdf()

        assert response["hypothesis_config"] == Any.dict.containing(
            {"appType": "via", "showHighlights": True}
        )

    @pytest.mark.parametrize(
        "value,expected",
        ((MISSING, False), (None, False), ("0", False), (True, True), ("1", True)),
    )
    def test_it_passes_open_sidebar_option(self, call_view_pdf, value, expected):
        params = {}
        if value is not self.MISSING:
            params["via.open_sidebar"] = value

        response = call_view_pdf(params=params)

        if expected:
            assert response["hypothesis_config"]["openSidebar"] is True

    @pytest.mark.parametrize(
        "value,expected",
        ((MISSING, None), (None, "None"), (0, "0"), ("anything", "anything")),
    )
    def test_it_passes_config_from_frame_option(self, call_view_pdf, value, expected):
        params = {}
        if value is not self.MISSING:
            params["via.request_config_from_frame"] = value

        response = call_view_pdf(params=params)

        if expected:
            assert response["hypothesis_config"]["requestConfigFromFrame"] == expected


@pytest.fixture
def call_view_pdf(make_request):
    def call_view_pdf(url="http://example.com/name.pdf", params=None):
        request = make_request(params=dict(params or {}, url=url))
        context = URLResource(request)
        return view_pdf(context, request)

    return call_view_pdf
