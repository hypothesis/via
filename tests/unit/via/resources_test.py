import pytest
from pyramid.httpexceptions import HTTPBadRequest

from via.resources import URLResource

NORMALISED_URLS = [
    # URLs that should be returned unchanged
    ("http://example.com", "http://example.com"),
    ("https://example.com", "https://example.com"),
    ("http://example.com?a=1", "http://example.com?a=1"),
    # URLs without a protocol that should have `https://` prefixed
    ("example.com", "https://example.com"),
    # Leading and trailing whitespace that should be stripped
    (" http://example.com", "http://example.com"),
    ("http://example.com ", "http://example.com"),
    # Check we remove Via stuff
    ("http://example.com?a=1&via.sec=TOKEN", "http://example.com?a=1"),
]


class TestURLResource:
    @pytest.mark.parametrize("url,expected", NORMALISED_URLS)
    def test_url_from_query_returns_url(self, pyramid_request, url, expected):
        pyramid_request.params["url"] = url
        context = URLResource(pyramid_request)

        assert context.url_from_query() == expected

    @pytest.mark.parametrize("params", ({}, {"urk": "foo"}, {"url": ""}))
    def test_url_from_query_raises_HTTPBadRequest_for_bad_urls(
        self, params, pyramid_request
    ):
        pyramid_request.params = params
        context = URLResource(pyramid_request)

        with pytest.raises(HTTPBadRequest):
            context.url_from_query()

    @pytest.mark.parametrize("url,expected", NORMALISED_URLS)
    def test_url_from_path_returns_url(self, pyramid_request, url, expected):
        pyramid_request.path_qs = f"/{url}"
        context = URLResource(pyramid_request)

        assert context.url_from_path() == expected

    @pytest.mark.parametrize("bad_path", ("/", "/  "))
    def test_url_from_path_raises_HTTPBadRequest_for_missing_urls(
        self, pyramid_request, bad_path
    ):
        pyramid_request.path_qs = bad_path
        context = URLResource(pyramid_request)

        with pytest.raises(HTTPBadRequest):
            context.url_from_path()
