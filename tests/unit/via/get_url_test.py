from io import BytesIO
from unittest.mock import sentinel

import pytest
from h_matchers import Any
from requests import Response
from requests.exceptions import SSLError

from via.exceptions import BadURL, UpstreamServiceError
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
        requests,
        response,
        content_type,
        mime_type,
        status_code,
    ):
        if content_type:
            response.headers = {"Content-Type": content_type}
        else:
            response.headers = {}

        response.status_code = status_code

        url = "http://example.com"

        result = get_url_details(url, headers=sentinel.headers)

        assert result == (mime_type, status_code)
        requests.get.assert_called_once_with(
            url, allow_redirects=True, stream=True, headers=Any(), timeout=10
        )

    @pytest.mark.usefixtures("response")
    def test_it_modifies_headers(self, requests, clean_headers, add_request_headers):
        get_url_details(url="http://example.com", headers={"X-Pre-Existing": 1})

        _args, kwargs = requests.get.call_args

        clean_headers.assert_called_once_with({"X-Pre-Existing": 1})
        add_request_headers.assert_called_once_with(clean_headers.return_value)
        assert kwargs["headers"] == add_request_headers.return_value

    def test_it_assumes_pdf_with_a_google_drive_url(self, requests):
        result = get_url_details(
            "https://drive.google.com/uc?id=--FILEID--&export=download"
        )

        assert result == ("application/pdf", 200)

        requests.get.assert_not_called()

    @pytest.mark.parametrize("bad_url", ("no-schema", "glub://example.com", "http://"))
    def test_it_raises_BadURL_for_invalid_urls(self, bad_url):
        with pytest.raises(BadURL):
            get_url_details(bad_url)

    def test_it_catches_requests_exceptions(self, requests):
        # We'll test one (of the many) error translations that `@handle_errors`
        # does for us to prove it's in use on the method.
        requests.get.side_effect = SSLError("Oh noe")

        with pytest.raises(UpstreamServiceError):
            get_url_details("http://example.com")

    @pytest.fixture
    def response(self, requests):
        response = Response()
        response.raw = BytesIO(b"")
        response.headers = {"Content-Type": "dummy"}
        response.status_code = 200
        requests.get.return_value = response

        return response

    @pytest.fixture
    def requests(self, patch):
        return patch("via.get_url.requests")

    @pytest.fixture(autouse=True)
    def add_request_headers(self, patch):
        return patch("via.get_url.add_request_headers", return_value={})

    @pytest.fixture(autouse=True)
    def clean_headers(self, patch):
        return patch("via.get_url.clean_headers", return_value={})
