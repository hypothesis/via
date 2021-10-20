from datetime import datetime, timedelta, timezone
from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPNoContent

from via.resources import QueryURLResource
from via.views.view_pdf import python_proxy_pdf_view, view_pdf


@pytest.mark.usefixtures(
    "secure_link_service",
    "google_drive_api",
    "proxy_pdf_service",
    "ms_one_drive_service",
)
class TestViewPDF:
    def test_it(self, call_view, pyramid_request, pyramid_settings, Configuration):
        response = call_view("http://example.com/foo.pdf")

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

    def test_it_signs_the_url_if_not_google(
        self,
        call_view,
        google_drive_api,
        quantized_expiry,
    ):
        google_drive_api.parse_file_url.return_value = None

        response = call_view("https://example.com/foo/bar.pdf?q=s")

        quantized_expiry.assert_called_once_with(max_age=timedelta(hours=25))
        signed_url = response["proxy_pdf_url"]
        signed_url_parts = signed_url.split("/")
        signature = signed_url_parts[5]
        expiry = signed_url_parts[6]
        assert signature == "qTq65RXvm6P2Y4bfzWdPzg"
        assert expiry == "1581183021"

    @pytest.mark.parametrize(
        "file_details,url",
        (
            (
                {"file_id": "FILE_ID"},
                "http://example.com/google_drive/FILE_ID/proxied.pdf"
                "?url=http%3A%2F%2Fgdrive%2Fdocument.pdf",
            ),
            (
                {"file_id": "FILE_ID", "resource_key": None},
                "http://example.com/google_drive/FILE_ID/proxied.pdf"
                "?url=http%3A%2F%2Fgdrive%2Fdocument.pdf",
            ),
            (
                {"file_id": "FILE_ID", "resource_key": "RESOURCE_KEY"},
                "http://example.com/google_drive/FILE_ID/RESOURCE_KEY/proxied.pdf"
                "?url=http%3A%2F%2Fgdrive%2Fdocument.pdf",
            ),
        ),
    )
    def test_it_signs_the_url_if_google(
        self, call_view, google_drive_api, secure_link_service, file_details, url
    ):
        google_drive_api.parse_file_url.return_value = file_details

        response = call_view("http://gdrive/document.pdf")

        secure_link_service.sign_url.assert_called_once_with(url)
        assert response["proxy_pdf_url"] == secure_link_service.sign_url.return_value

    def test_it_signs_the_url_if_ms_one_drive(
        self,
        call_view,
        pyramid_request,
        ms_one_drive_service,
        secure_link_service,
    ):
        url = "http://ms_one_drive_url/document.pdf"
        ms_one_drive_service.is_one_drive_url.return_value = True

        response = call_view(url)

        secure_link_service.sign_url.assert_called_once_with(
            pyramid_request.route_url("python_proxy_pdf", _query={"url": url})
        )
        assert response["proxy_pdf_url"] == secure_link_service.sign_url.return_value

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
        google_drive_api.parse_file_url.return_value = None

        return google_drive_api

    @pytest.fixture(autouse=True)
    def ms_one_drive_service(self, ms_one_drive_service):
        ms_one_drive_service.is_one_drive_url.return_value = False

        return ms_one_drive_service

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


class TestPythonProxyPdf:
    def test_it(self, call_view, proxy_pdf_service):
        url = "https://onedriveurl.com"
        proxy_pdf_service.iter_url.return_value = range(5)

        response = call_view(url, view=python_proxy_pdf_view)

        assert response.app_iter == range(5)

    def test_empty_pdf(self, call_view, proxy_pdf_service):
        url = "https://onedriveurl.com"
        proxy_pdf_service.iter_url.return_value = None

        response = call_view(url, view=python_proxy_pdf_view)

        assert isinstance(response, HTTPNoContent)


@pytest.fixture
def call_view(pyramid_request):
    def call_view(url="http://example.com/name.pdf", params=None, view=view_pdf):
        pyramid_request.params = dict(params or {}, url=url)
        context = QueryURLResource(pyramid_request)
        return view(context, pyramid_request)

    return call_view
