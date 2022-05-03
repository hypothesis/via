from unittest.mock import sentinel

import pytest

from via.requests_tools.headers import add_request_headers
from via.services.jstor import JSTORAPI, factory


class TestJSTORAPI:
    @pytest.mark.parametrize(
        "api_url,expected", [(None, False), ("http://jstor-api.com", True)]
    )
    def test_enabled(self, api_url, expected):
        svc = JSTORAPI(api_url=api_url, http_service=sentinel.http)

        assert svc.enabled == expected

    @pytest.mark.parametrize(
        "url,is_jstor", (("jstor://anything", True), ("http://other", False))
    )
    def test_is_jstor_url(self, svc, url, is_jstor):
        assert svc.is_jstor_url(url) == is_jstor

    @pytest.mark.parametrize(
        "url,expected",
        [
            ("jstor://ARTICLE_ID", "http://jstor.example.com/10.2307/ARTICLE_ID?ip=IP"),
            ("jstor://PREFIX/SUFFIX", "http://jstor.example.com/PREFIX/SUFFIX?ip=IP"),
        ],
    )
    def test_stream_pdf(self, svc, http_service, url, expected):
        stream = svc.stream_pdf(url, "IP")

        http_service.stream.assert_called_once_with(
            expected, headers=add_request_headers({"Accept": "application/pdf"})
        )
        assert stream == http_service.stream.return_value

    @pytest.fixture
    def svc(self, http_service):
        return JSTORAPI(api_url="http://jstor.example.com", http_service=http_service)


class TestFactory:
    def test_it(self, pyramid_request, JSTORAPI, http_service):
        pyramid_request.registry.settings["jstor_pdf_url"] = sentinel.jstor_pdf_url

        svc = factory(sentinel.context, pyramid_request)

        JSTORAPI.assert_called_once_with(
            http_service=http_service, api_url=sentinel.jstor_pdf_url
        )
        assert svc == JSTORAPI.return_value

    @pytest.fixture
    def JSTORAPI(self, patch):
        return patch("via.services.jstor.JSTORAPI")
