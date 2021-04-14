import pytest
from pyramid.httpexceptions import HTTPBadRequest

from via.resources import URLResource


class TestURLResource:
    def test_it_returns_url(self, pyramid_request):
        url = pyramid_request.params["url"] = "http://example.com"
        context = URLResource(pyramid_request)

        assert context.url() == url

    @pytest.mark.parametrize("params", ({}, {"urk": "foo"}, {"url": ""}))
    def test_it_raises_HTTPBadRequest_for_bad_urls(self, params, pyramid_request):
        pyramid_request.params = params
        context = URLResource(pyramid_request)

        with pytest.raises(HTTPBadRequest):
            context.url()
