import json
from unittest.mock import sentinel

import pytest
from h_matchers import Any
from markupsafe import Markup

from via.resources import URLResource
from via.views.view_pdf import view_pdf


class TestViewPDF:
    def test_it_passes_through_static_config(self, call_view_pdf, pyramid_settings):
        response = call_view_pdf()

        assert response == Any.dict.containing(
            {
                "client_embed_url": json.dumps(pyramid_settings["client_embed_url"]),
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
    def test_we_pass_through_the_url_exactly_as_a_quoted_json_string(
        self, call_view_pdf, pdf_url, pyramid_settings
    ):
        response = call_view_pdf(pdf_url)

        assert response["pdf_url"] == json.dumps(
            f"{pyramid_settings['nginx_server']}/proxy/static/{pdf_url}"
        )

        # Check we disable Jinja 2 escaping
        assert isinstance(response["pdf_url"], Markup)

    def test_we_escape_quote_literals_in_urls_to_prevent_XSS(
        self, call_view_pdf, pyramid_settings
    ):
        response = call_view_pdf('a"b')
        assert response["pdf_url"] == json.dumps(
            f"{pyramid_settings['nginx_server']}/proxy/static/a\"b"
        )

    def test_it_extracts_config(self, call_view_pdf, Configuration):
        response = call_view_pdf()

        Configuration.extract_from_params.assert_called_once_with(
            Any.mapping.containing({"url": Any.string()})
        )

        assert response["hypothesis_config"] == sentinel.h_config

    @pytest.fixture
    def Configuration(self, patch):
        Configuration = patch("via.views.view_pdf.Configuration")
        Configuration.extract_from_params.return_value = (
            sentinel.via_config,
            sentinel.h_config,
        )
        return Configuration

    @pytest.fixture
    def call_view_pdf(self, make_request):
        def call_view_pdf(url="http://example.com/name.pdf", params=None):
            request = make_request(params=dict(params or {}, url=url))
            context = URLResource(request)
            return view_pdf(context, request)

        return call_view_pdf
