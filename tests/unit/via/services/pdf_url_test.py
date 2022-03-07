from datetime import datetime, timedelta, timezone
from unittest.mock import sentinel

import pytest

from via.services.pdf_url import PDFURLBuilder, _NGINXSigner, factory


class TestNGINXSigner:
    def test_it(
        self,
        svc,
        quantized_expiry,
    ):
        signed_url = svc.sign_url(
            "https://example.com/foo/bar.pdf?q=s", "/proxy/static/"
        )

        quantized_expiry.assert_called_once_with(max_age=timedelta(hours=25))
        signed_url_parts = signed_url.split("/")
        signature = signed_url_parts[5]
        expiry = signed_url_parts[6]
        assert signature == "qTq65RXvm6P2Y4bfzWdPzg"
        assert expiry == "1581183021"

    @pytest.fixture
    def svc(self, pyramid_settings):
        return _NGINXSigner(
            pyramid_settings["nginx_server"],
            pyramid_settings["nginx_secure_link_secret"],
        )

    @pytest.fixture(autouse=True)
    def quantized_expiry(self, patch):
        return patch(
            "via.services.pdf_url.quantized_expiry",
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


class TestPDFURLBuilder:
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
    def test_google_file_url(
        self, svc, google_drive_api, secure_link_service, file_details, url
    ):
        google_drive_api.parse_file_url.return_value = file_details

        pdf_url = svc.get_pdf_url("http://gdrive/document.pdf")

        secure_link_service.sign_url.assert_called_once_with(url)
        assert pdf_url == secure_link_service.sign_url.return_value

    @pytest.mark.parametrize(
        "url,endpoint_url",
        (
            # pylint:disable=line-too-long
            (
                "https://my-sharepoint.sharepoint.com/FILE_ID/?download=1",
                "http://example.com/onedrive/proxied.pdf?url=https%3A%2F%2Fmy-sharepoint.sharepoint.com%2FFILE_ID%2F%3Fdownload%3D1",
            ),
            (
                "https://api.onedrive.com/v1.0/FILE_ID/root/content",
                "http://example.com/onedrive/proxied.pdf?url=https%3A%2F%2Fapi.onedrive.com%2Fv1.0%2FFILE_ID%2Froot%2Fcontent",
            ),
        ),
    )
    def test_onedrive_url(
        self, svc, secure_link_service, google_drive_api, url, endpoint_url
    ):
        google_drive_api.parse_file_url.return_value = None

        pdf_url = svc.get_pdf_url(url)

        secure_link_service.sign_url.assert_called_once_with(endpoint_url)
        assert pdf_url == secure_link_service.sign_url.return_value

    def test_jstor_url(
        self, svc, secure_link_service, google_drive_api, pyramid_request
    ):
        google_drive_api.parse_file_url.return_value = None
        pyramid_request.params["jstor.ip"] = "1.1.1.1"

        pdf_url = svc.get_pdf_url("jstor://DOI")

        secure_link_service.sign_url.assert_called_once_with(
            "http://example.com/jstor/proxied.pdf?url=jstor%3A%2F%2FDOI&jstor.ip=1.1.1.1"
        )
        assert pdf_url == secure_link_service.sign_url.return_value

    def test_nginx_file_url(self, google_drive_api, svc):
        google_drive_api.parse_file_url.return_value = None

        pdf_url = svc.get_pdf_url("http://nginx/document.pdf")

        svc.nginx_signer.sign_url.assert_called_once_with(
            "http://nginx/document.pdf", nginx_path="/proxy/static/"
        )
        assert pdf_url == svc.nginx_signer.sign_url.return_value

    @pytest.fixture
    def svc(
        self,
        google_drive_api,
        secure_link_service,
        pyramid_request,
        PatchedNGINXSigner,
        jstor_api,
    ):
        return PDFURLBuilder(
            pyramid_request,
            google_drive_api,
            jstor_api,
            secure_link_service,
            pyramid_request.route_url,
            PatchedNGINXSigner.return_value,
        )


class TestFactory:
    def test_it(
        self,
        pyramid_request,
        pyramid_settings,
        PDFURLBuilder,
        PatchedNGINXSigner,
        google_drive_api,
        secure_link_service,
        jstor_api,
    ):
        svc = factory(sentinel.context, pyramid_request)

        PatchedNGINXSigner.assert_called_once_with(
            nginx_server=pyramid_settings["nginx_server"],
            secret=pyramid_settings["nginx_secure_link_secret"],
        )
        PDFURLBuilder.assert_called_once_with(
            request=pyramid_request,
            google_drive_api=google_drive_api,
            jstor_api=jstor_api,
            secure_link_service=secure_link_service,
            route_url=pyramid_request.route_url,
            nginx_signer=PatchedNGINXSigner.return_value,
        )
        assert svc == PDFURLBuilder.return_value

    @pytest.fixture
    def PDFURLBuilder(self, patch):
        return patch("via.services.pdf_url.PDFURLBuilder")


@pytest.fixture
def PatchedNGINXSigner(patch):
    return patch("via.services.pdf_url._NGINXSigner")
