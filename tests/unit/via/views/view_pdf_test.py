from datetime import datetime, timedelta, timezone
from unittest.mock import sentinel

import pytest
from h_matchers import Any

from via.resources import URLResource
from via.views.view_pdf import view_pdf


@pytest.mark.usefixtures("secure_link_service", "google_drive_api")
class TestViewPDF:
    def test_it(self, call_view_pdf, pyramid_request, pyramid_settings, Configuration):
        response = call_view_pdf("http://example.com/foo.pdf")

        Configuration.extract_from_params.assert_called_once_with(
            pyramid_request.params
        )
        pyramid_request.checkmate.raise_if_blocked(sentinel.url)

        assert response == {
            "pdf_url": "http://example.com/foo.pdf",
            "proxy_pdf_url": Any(),
            "client_embed_url": pyramid_settings["client_embed_url"],
            "static_url": pyramid_request.static_url,
            "hypothesis_config": sentinel.h_config,
        }

    @pytest.mark.parametrize(
        "drive_available,is_google_url", ((True, False), (False, True), (False, False))
    )
    def test_it_signs_the_url_if_not_google(
        self,
        call_view_pdf,
        google_drive_api,
        secure_link_service,
        drive_available,
        is_google_url,
        quantized_expiry,
    ):
        google_drive_api.is_available = drive_available
        google_drive_api.google_drive_id.return_value = (
            sentinel.file_id if is_google_url else None
        )

        response = call_view_pdf("https://example.com/foo/bar.pdf?q=s")

        quantized_expiry.assert_called_once_with(max_age=timedelta(hours=25))
        signed_url = response["proxy_pdf_url"]
        signed_url_parts = signed_url.split("/")
        signature = signed_url_parts[5]
        expiry = signed_url_parts[6]
        assert signature == "qTq65RXvm6P2Y4bfzWdPzg"
        assert expiry == "1581183021"

    def test_it_signs_the_url_if_google(
        self, call_view_pdf, google_drive_api, secure_link_service
    ):
        google_drive_api.is_available = True
        google_drive_api.google_drive_id.return_value = "FILE_ID"

        response = call_view_pdf(sentinel.url)

        secure_link_service.sign_url.assert_called_once_with(
            "http://example.com/google_drive/FILE_ID/proxied.pdf?url=sentinel.url"
        )
        assert response["proxy_pdf_url"] == secure_link_service.sign_url.return_value

    @pytest.fixture
    def call_view_pdf(self, pyramid_request):
        def call_view_pdf(url="http://example.com/name.pdf", params=None):
            pyramid_request.params = dict(params or {}, url=url)
            context = URLResource(pyramid_request)
            return view_pdf(context, pyramid_request)

        return call_view_pdf

    @pytest.fixture
    def Configuration(self, patch):
        Configuration = patch("via.views.view_pdf.Configuration")
        Configuration.extract_from_params.return_value = (
            sentinel.via_config,
            sentinel.h_config,
        )

        return Configuration

    @pytest.fixture(autouse=True)
    def google_drive_api(self, google_drive_api):
        google_drive_api.google_drive_id.return_value = None

        return google_drive_api

    @pytest.fixture(autouse=True)
    def quantized_expiry(self, patch):
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
