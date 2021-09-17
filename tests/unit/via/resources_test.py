from unittest.mock import create_autospec

import pytest
from pyramid.httpexceptions import HTTPBadRequest

from via.exceptions import BadURL
from via.resources import PathURLResource, QueryURLResource, get_original_url

NORMALISED_URLS = [
    # URLs that should be returned unchanged
    ("http://example.com", "http://example.com"),
    ("https://example.com", "https://example.com"),
    ("ftp://example.com", "ftp://example.com"),
    ("http://example.com?a=1", "http://example.com?a=1"),
    # URLs without a protocol that should have `https://` prefixed
    ("example.com", "https://example.com"),
    (".example.com", "https://example.com"),
    ("//example.com", "https://example.com"),
    # Leading and trailing whitespace that should be stripped
    (" http://example.com", "http://example.com"),
    ("http://example.com ", "http://example.com"),
    # Check we remove Via stuff
    ("http://example.com?a=1&via.sec=TOKEN", "http://example.com?a=1"),
]


class TestQueryURLResource:
    @pytest.mark.parametrize("url,expected", NORMALISED_URLS)
    def test_url_from_query_returns_url(self, context, pyramid_request, url, expected):
        pyramid_request.params["url"] = url

        assert context.url_from_query() == expected

    @pytest.mark.parametrize("params", ({}, {"urk": "foo"}, {"url": ""}))
    def test_url_from_query_raises_HTTPBadRequest_for_bad_urls(
        self, context, pyramid_request, params
    ):
        pyramid_request.params = params

        with pytest.raises(HTTPBadRequest):
            context.url_from_query()

    def test_url_from_raises_BadURL_for_malformed_urls(self, context, pyramid_request):
        pyramid_request.params["url"] = "]"

        with pytest.raises(BadURL):
            context.url_from_query()

    @pytest.fixture
    def context(self, pyramid_request):
        return QueryURLResource(pyramid_request)


class TestPathURLResource:
    @pytest.mark.parametrize("url,expected", NORMALISED_URLS)
    def test_url_from_path_returns_url(self, context, pyramid_request, url, expected):
        pyramid_request.path_qs = f"/{url}"

        assert context.url_from_path() == expected

    @pytest.mark.parametrize("bad_path", ("/", "/  "))
    def test_url_from_path_raises_HTTPBadRequest_for_missing_urls(
        self, context, pyramid_request, bad_path
    ):
        pyramid_request.path_qs = bad_path

        with pytest.raises(HTTPBadRequest):
            context.url_from_path()

    def test_url_from_path_BadURL_for_malformed_urls(self, context, pyramid_request):
        pyramid_request.path_qs = "/]"

        with pytest.raises(BadURL):
            context.url_from_path()

    @pytest.fixture
    def context(self, pyramid_request):
        return PathURLResource(pyramid_request)


class TestGetOriginalURL:
    def test_it_with_paths(self, path_url_resource):
        assert (
            get_original_url(path_url_resource)
            == path_url_resource.url_from_path.return_value
        )

    @pytest.mark.parametrize(
        "exc,expected", ((HTTPBadRequest, None), (BadURL("message", url="url"), "url"))
    )
    def test_it_with_bad_paths(self, path_url_resource, exc, expected):
        path_url_resource.url_from_path.side_effect = exc

        assert get_original_url(path_url_resource) == expected

    def test_it_with_queries(self, query_url_resource):
        assert (
            get_original_url(query_url_resource)
            == query_url_resource.url_from_query.return_value
        )

    @pytest.mark.parametrize(
        "exc,expected", ((HTTPBadRequest, None), (BadURL("message", url="url"), "url"))
    )
    def test_it_with_bad_queries(self, query_url_resource, exc, expected):
        query_url_resource.url_from_query.side_effect = exc

        assert get_original_url(query_url_resource) == expected

    def test_it_with_non_resource(self):
        assert get_original_url(None) is None

    @pytest.fixture
    def path_url_resource(self):
        return create_autospec(PathURLResource, spec_set=True, instance=True)

    @pytest.fixture
    def query_url_resource(self):
        return create_autospec(QueryURLResource, spec_set=True, instance=True)
