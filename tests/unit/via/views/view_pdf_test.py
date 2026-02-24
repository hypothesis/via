from unittest.mock import create_autospec, sentinel

import pytest

from via.resources import QueryURLResource
from via.views.view_pdf import proxy_google_drive_file, proxy_python_pdf, view_pdf


class TestViewPDF:
    def test_it_returns_restricted_page_when_not_lms(
        self, context, pyramid_request, secure_link_service
    ):
        secure_link_service.request_has_valid_token.return_value = False
        context.url_from_query.return_value = "http://example.com/foo.pdf"

        result = view_pdf(context, pyramid_request)

        assert result == {"target_url": "http://example.com/foo.pdf"}
        assert pyramid_request.override_renderer == "via:templates/restricted.html.jinja2"

    def test_it_returns_restricted_none_url_on_error_when_not_lms(
        self, context, pyramid_request, secure_link_service
    ):
        secure_link_service.request_has_valid_token.return_value = False
        context.url_from_query.side_effect = Exception("bad url")

        result = view_pdf(context, pyramid_request)

        assert result == {"target_url": None}

    def test_it_serves_pdf_when_lms(
        self, context, pyramid_request, secure_link_service, checkmate_service, pdf_url_builder_service
    ):
        secure_link_service.request_has_valid_token.return_value = True
        context.url_from_query.return_value = "http://example.com/foo.pdf"
        pyramid_request.params["url"] = "http://example.com/foo.pdf"

        result = view_pdf(context, pyramid_request)

        assert "pdf_url" in result
        assert result["pdf_url"] == "http://example.com/foo.pdf"

    @pytest.fixture
    def context(self):
        return create_autospec(QueryURLResource, spec_set=True, instance=True)


class TestProxyGoogleDriveFile:
    def test_it_returns_restricted_page_when_not_lms(
        self, pyramid_request, secure_link_service
    ):
        secure_link_service.request_has_valid_token.return_value = False

        response = proxy_google_drive_file(pyramid_request)

        assert response == {"target_url": None}

    def test_it_proxies_when_lms(
        self, pyramid_request, secure_link_service, google_drive_api
    ):
        secure_link_service.request_has_valid_token.return_value = True
        pyramid_request.matchdict = {"file_id": "test_file_id"}
        google_drive_api.iter_file.return_value = iter([b"pdf content"])

        result = proxy_google_drive_file(pyramid_request)

        google_drive_api.iter_file.assert_called_once_with(
            file_id="test_file_id", resource_key=None
        )


class TestProxyPythonPDF:
    def test_it_returns_restricted_page_when_not_lms(
        self, pyramid_request, secure_link_service
    ):
        secure_link_service.request_has_valid_token.return_value = False
        context = create_autospec(QueryURLResource, spec_set=True, instance=True)
        context.url_from_query.return_value = "https://one-drive.com"

        response = proxy_python_pdf(context, pyramid_request)

        assert response == {"target_url": "https://one-drive.com"}

    def test_it_proxies_when_lms(
        self, pyramid_request, secure_link_service, http_service
    ):
        secure_link_service.request_has_valid_token.return_value = True
        context = create_autospec(QueryURLResource, spec_set=True, instance=True)
        context.url_from_query.return_value = "https://one-drive.com"
        http_service.stream.return_value = iter([b"pdf content"])

        result = proxy_python_pdf(context, pyramid_request)

        http_service.stream.assert_called_once()
