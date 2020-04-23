import pytest
from pyramid.httpexceptions import HTTPBadRequest

from via.resources import URLResource


class TestURLResource:
    def test_it_returns_url(self, make_request):
        url = "http://example.com"
        context = URLResource(make_request(params={"url": url}))

        assert context.url() == url

    @pytest.mark.parametrize("params", ({}, {"urk": "foo"}, {"url": ""}))
    def test_it_raises_HTTPBadRequest_for_bad_urls(self, params, make_request):
        request = make_request(params=params)
        context = URLResource(request)

        with pytest.raises(HTTPBadRequest):
            context.url()
