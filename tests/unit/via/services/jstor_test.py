import base64
from unittest.mock import sentinel

import pytest
from faker import Faker

from via.requests_tools.headers import add_request_headers
from via.services.jstor import JSTORAPI, decode_base64_stream, factory


class TestJSTORAPI:
    @pytest.mark.parametrize(
        "api_url,expected", [(None, False), ("http://jstor-api.com", True)]
    )
    def test_enabled(self, api_url, expected):
        svc = JSTORAPI(api_url=api_url, http_service=sentinel.http)

        assert svc.enabled == expected

    @pytest.mark.parametrize(
        "url,is_jstor", (("jstor://anything", True), ("http://example.com", False))
    )
    def test_is_jstor_url(self, url, is_jstor):
        assert JSTORAPI.is_jstor_url(url) == is_jstor

    @pytest.mark.parametrize(
        "url,expected",
        [
            ("jstor://ARTICLE_ID", "http://jstor.example.com/10.2307/ARTICLE_ID?ip=IP"),
            ("jstor://PREFIX/SUFFIX", "http://jstor.example.com/PREFIX/SUFFIX?ip=IP"),
        ],
    )
    def test_stream_pdf(self, svc, decode_base64_stream, http_service, url, expected):
        stream = svc.stream_pdf(url, "IP")

        http_service.stream.assert_called_once_with(
            expected, headers=add_request_headers({"Accept": "application/pdf"})
        )
        decode_base64_stream.assert_called_once_with(http_service.stream.return_value)
        assert stream == decode_base64_stream.return_value

    @pytest.fixture
    def decode_base64_stream(self, patch):
        return patch("via.services.jstor.decode_base64_stream")

    @pytest.fixture
    def svc(self, http_service):
        return JSTORAPI(api_url="http://jstor.example.com", http_service=http_service)


class TestDecodeBase64Stream:
    def test_it(self, content_string, base64_stream):
        content_iter = decode_base64_stream(base64_stream)

        decoded_content = b"".join(content_iter).decode("utf-8")
        assert decoded_content == content_string

    def test_it_with_non_padded_strings(self):
        # Non padded strings could leave us with left overs when we are
        # finished iterating.
        string = "Hello"
        b64 = base64.b64encode(string.encode("utf-8")).rstrip(b"=")
        assert len(b64) % 4, "Sanity check we are not divisible by 4"

        content_iter = decode_base64_stream([b64])

        decoded_content = b"".join(content_iter).decode("utf-8")
        assert decoded_content == string

    @pytest.fixture
    def content_string(self):
        random_text = Faker().paragraph(nb_sentences=100)
        # Replace lots of chars with the UTF-8 snowman to prove we can handle
        # high valued chars as well as ASCII
        random_text = random_text.replace("e", "☃")

        return random_text

    @pytest.fixture
    def base64_stream(self, content_string):
        # We can't yield directly from this method as pytest will think we
        # are creating a context manager like situation. So use a sub-function
        def _chunk(raw_bytes, chunk_size=129):
            for i in range(len(raw_bytes) // chunk_size + 1):
                # Yield random empty bits to test our handling of that
                yield b""
                yield raw_bytes[i * chunk_size : (i + 1) * chunk_size]

        return _chunk(base64.b64encode(content_string.encode("utf-8")))


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
