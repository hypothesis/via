import pytest
from pyramid.httpexceptions import HTTPBadRequest

from via.resources import URLRoute


class TestURLRoute:
    def test_it_returns_url(self, make_request):
        url = "http://example.com"
        context = URLRoute(make_request(params={"url": url}))

        assert context.url == url

    @pytest.mark.parametrize("params", ({}, {"urk": "foo"}, {"url": ""}))
    def test_it_raises_HTTPBadRequest_for_bad_urls(self, params, make_request):
        request = make_request(params=params)
        context = URLRoute(request)

        with pytest.raises(HTTPBadRequest):
            context.url  # pylint: disable=pointless-statement
