from io import BytesIO

import pytest
from h_matchers import Any
from requests import Response
from requests.exceptions import (
    MissingSchema,
    ProxyError,
    SSLError,
    UnrewindableBodyError,
)

from via.exceptions import BadURL, UnhandledException, UpstreamServiceError
from via.get_url_details import get_url_details


class TestGetURLDetails:
    GOOGLE_API_KEY = "google_api_key"

    @pytest.mark.parametrize(
        "content_type,status_code", (("text/html", 501), ("application/pdf", 200))
    )
    def test_it_calls_get_for_normal_urls(self, requests, content_type, status_code):
        requests.get.return_value = self._make_response(content_type, status_code)
        url = "http://example.com"

        result = get_url_details(url)

        assert result == (content_type, status_code)
        requests.get.assert_called_once_with(url, allow_redirects=True, stream=True)

    def test_it_assumes_google_documents_are_pdfs_without_an_api_key(
        self, requests, google_drive_url
    ):
        result = get_url_details(google_drive_url)

        assert result == ("application/pdf", 200)
        requests.get.assert_not_called()

    @pytest.mark.usefixtures("with_api_key")
    def test_it_calls_google_drive_api_with_api_key(self, requests, google_drive_url):
        requests.get.return_value = self._make_response(
            content_type="application/json", body='{"mimeType": "application/pdf"}'
        )

        get_url_details(google_drive_url)

        requests.get.assert_called_once_with(
            Any.url.matching(
                "https://www.googleapis.com/drive/v3/files/--FILEID--"
            ).with_query({"key": self.GOOGLE_API_KEY})
        )

    @pytest.mark.usefixtures("with_api_key")
    def test_it_handles_bad_google_json_responses(self, requests, google_drive_url):
        requests.get.return_value = self._make_response(
            content_type="application/json", body="{"
        )

        with pytest.raises(UpstreamServiceError):
            get_url_details(google_drive_url)

    @pytest.fixture
    def google_drive_url(self):
        return "https://drive.google.com/uc?id=--FILEID--&export=download"

    @pytest.mark.parametrize("bad_url", ("no-schema", "glub://example.com", "http://"))
    def test_it_raises_BadURL_for_invalid_urls(self, bad_url):
        with pytest.raises(BadURL):
            get_url_details(bad_url)

    @pytest.mark.parametrize(
        "request_exception,expected_exception",
        (
            (MissingSchema, BadURL),
            (ProxyError, UpstreamServiceError),
            (SSLError, UpstreamServiceError),
            (UnrewindableBodyError, UnhandledException),
        ),
    )
    def test_it_catches_requests_exceptions(
        self, requests, request_exception, expected_exception
    ):
        requests.get.side_effect = request_exception("Oh noe")

        with pytest.raises(expected_exception):
            get_url_details("http://example.com")

    @staticmethod
    def _make_response(content_type="application/pdf", status_code=200, body=None):
        response = Response()

        response.raw = BytesIO(body.encode("utf-8") if body else b"")
        response.headers = {"Content-Type": content_type}
        response.status_code = status_code

        return response

    @pytest.fixture
    def with_api_key(self, patch):
        api_key = patch("via.get_url_details.GOOGLE_DRIVE_API_KEY")
        api_key.__str__.return_value = self.GOOGLE_API_KEY

    @pytest.fixture
    def requests(self, patch):
        return patch("via.get_url_details.requests")
