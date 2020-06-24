from io import BytesIO

import pytest
from mock import sentinel
from requests import Response
from requests.exceptions import (
    MissingSchema,
    ProxyError,
    SSLError,
    UnrewindableBodyError,
)

from via.exceptions import BadURL, UnhandledException, UpstreamServiceError
from via.get_url_details import BACKUP_USER_AGENT, get_url_details


class TestGetURLDetails:
    @pytest.mark.parametrize(
        "content_type,status_code", (("text/html", 501), ("application/pdf", 200))
    )
    def test_it_calls_get_for_normal_urls(self, requests, content_type, status_code):
        response = Response()
        response.raw = BytesIO(b"")
        response.headers = {"Content-Type": content_type}
        response.status_code = status_code
        requests.get.return_value = response

        url = "http://example.com"

        result = get_url_details(
            url,
            headers={"User-Agent": sentinel.user_agent, "Other-Nonsense": "ignored"},
        )

        assert result == (content_type, status_code)
        requests.get.assert_called_once_with(
            url,
            allow_redirects=True,
            stream=True,
            headers={"User-Agent": sentinel.user_agent},
        )

    def test_it_assumes_pdf_with_a_google_drive_url(self, requests):
        result = get_url_details(
            "https://drive.google.com/uc?id=--FILEID--&export=download", {}
        )

        assert result == ("application/pdf", 200)

        requests.get.assert_not_called()

    @pytest.mark.parametrize("bad_url", ("no-schema", "glub://example.com", "http://"))
    def test_it_raises_BadURL_for_invalid_urls(self, bad_url):
        with pytest.raises(BadURL):
            get_url_details(bad_url, {})

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
            get_url_details("http://example.com", {})

    def test_it_uses_default_user_agent_if_none_found(self, requests):
        get_url_details("http://example.com", {})

        _, kwargs = requests.get.call_args
        assert kwargs["headers"] == {"User-Agent": BACKUP_USER_AGENT}

    @pytest.fixture
    def requests(self, patch):
        return patch("via.get_url_details.requests")
