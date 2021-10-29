from io import BytesIO
from unittest.mock import sentinel

import pytest
from h_matchers import Any
from requests import Response

from via.get_url import get_url_details


class TestGetURLDetails:
    @pytest.mark.parametrize(
        "content_type,mime_type,status_code",
        (
            ("text/html", "text/html", 501),
            ("application/pdf", "application/pdf", 200),
            ("application/pdf; qs=0.001", "application/pdf", 201),
            (None, None, 301),
        ),
    )
    def test_it_calls_get_for_normal_urls(
        # pylint: disable=too-many-arguments
        self,
        response,
        content_type,
        mime_type,
        status_code,
        http_service,
    ):
        if content_type:
            response.headers = {"Content-Type": content_type}
        else:
            response.headers = {}

        response.status_code = status_code

        url = "http://example.com"

        result = get_url_details(http_service, url, headers=sentinel.headers)

        assert result == (mime_type, status_code)
        http_service.get.assert_called_once_with(
            url,
            allow_redirects=True,
            stream=True,
            headers=Any(),
            timeout=10,
            raise_for_status=False,
        )

    @pytest.mark.usefixtures("response")
    def test_it_modifies_headers(
        self, clean_headers, add_request_headers, http_service
    ):
        get_url_details(
            http_service, url="http://example.com", headers={"X-Pre-Existing": 1}
        )

        _args, kwargs = http_service.get.call_args

        clean_headers.assert_called_once_with({"X-Pre-Existing": 1})
        add_request_headers.assert_called_once_with(clean_headers.return_value)
        assert kwargs["headers"] == add_request_headers.return_value

    def test_it_assumes_pdf_with_a_google_drive_url(self, http_service, GoogleDriveAPI):
        GoogleDriveAPI.parse_file_url.return_value = {"file_id": "FILE_ID"}

        result = get_url_details(http_service, sentinel.google_drive_url)

        assert result == ("application/pdf", 200)
        GoogleDriveAPI.parse_file_url.assert_called_once_with(sentinel.google_drive_url)
        http_service.get.assert_not_called()

    @pytest.fixture
    def response(self, http_service):
        response = Response()
        response.raw = BytesIO(b"")
        response.headers = {"Content-Type": "dummy"}
        response.status_code = 200
        http_service.get.return_value = response

        return response

    @pytest.fixture
    def GoogleDriveAPI(self, patch):
        return patch("via.get_url.GoogleDriveAPI", return_value={})

    @pytest.fixture(autouse=True)
    def add_request_headers(self, patch):
        return patch("via.get_url.add_request_headers", return_value={})

    @pytest.fixture(autouse=True)
    def clean_headers(self, patch):
        return patch("via.get_url.clean_headers", return_value={})
