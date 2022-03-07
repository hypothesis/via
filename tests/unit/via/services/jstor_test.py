from unittest.mock import sentinel

import pytest

from via.requests_tools.headers import add_request_headers
from via.services.jstor import JSTORAPI, factory


class TestJSTORAPI:
    @pytest.mark.parametrize(
        "url,expected", [(None, False), ("http://jstor-api.com", True)]
    )
    def test_enabled(self, url, expected):
        assert JSTORAPI(sentinel.http, url).enabled == expected

    @pytest.mark.parametrize(
        "url,expected",
        [
            ("jstor://ARTICLE_ID", "http://jstor-api.com/10.2307/ARTICLE_ID?ip=IP"),
            ("jstor://PREFIX/SUFFIX", "http://jstor-api.com/PREFIX/SUFFIX?ip=IP"),
        ],
    )
    def test_pdf_stream(self, http_service, url, expected):
        stream = JSTORAPI(http_service, "http://jstor-api.com").jstor_pdf_stream(
            url, "IP"
        )

        http_service.stream.assert_called_once_with(
            expected, headers=add_request_headers({"Accept": "application/pdf"})
        )
        assert stream == http_service.stream.return_value


class TestFactory:
    @pytest.mark.usefixtures("http_service")
    def test_it(self, pyramid_request):
        assert isinstance(factory(sentinel.context, pyramid_request), JSTORAPI)
