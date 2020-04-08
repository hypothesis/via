from io import BytesIO

import pytest
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
    @pytest.mark.parametrize(
        "content_type,status_code", (("text/html", 501), ("application/pdf", 200))
    )
    def test_it_calls_get_for_normal_urls(self, requests, content_type, status_code):
        requests.get.return_value = self._make_response(content_type, status_code)
        url = "http://example.com"

        result = get_url_details(url)
 
        assert result == (content_type, status_code)
        requests.get.assert_called_once_with(url, allow_redirects=True, stream=True)

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
    def requests(self, patch):
        return patch("via.get_url_details.requests")
