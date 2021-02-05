import json
from datetime import datetime, timedelta, timezone
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

    def test_it_signs_the_url(self, call_view_pdf, quantized_expiry):
        response = call_view_pdf("https://example.com/foo/bar.pdf?q=s")

        quantized_expiry.assert_called_once_with(max_age=timedelta(hours=2))
        signed_url = json.loads(response["pdf_url"])
        signed_url_parts = signed_url.split("/")
        signature = signed_url_parts[5]
        expiry = signed_url_parts[6]
        assert signature == "qTq65RXvm6P2Y4bfzWdPzg"
        assert expiry == "1581183021"

    @pytest.mark.parametrize(
        "pdf_url",
        [
            "http://example.com/foo.pdf",
            "http://example.com/foo.pdf?a=1&a=2",
            "http://example.com/foo%2C.pdf?a=1&a=2",
        ],
    )
    def test_it_passes_through_the_url_exactly_as_a_quoted_json_string(
        self, call_view_pdf, pdf_url, pyramid_settings
    ):
        response = call_view_pdf(pdf_url)

        assert json.loads(response["pdf_url"]).endswith(f"/{pdf_url}")

        # Check we disable Jinja 2 escaping
        assert isinstance(response["pdf_url"], Markup)

    def test_it_escapes_quote_literals_in_urls_to_prevent_XSS(
        self, call_view_pdf, pyramid_settings
    ):
        response = call_view_pdf('a"b')

        assert json.loads(response["pdf_url"]).endswith('a"b')

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


@pytest.fixture(autouse=True)
def quantized_expiry(patch):
    return patch(
        "via.views.view_pdf.quantized_expiry",
        return_value=datetime(
            year=2020,
            month=2,
            day=8,
            hour=17,
            minute=30,
            second=21,
            tzinfo=timezone.utc,
        ),
    )
