from unittest.mock import create_autospec, sentinel

import pytest
from pyramid.httpexceptions import HTTPGone

from via.resources import PathURLResource
from via.views.proxy import proxy, static_fallback


class TestStaticFallback:
    def test_it(self):
        with pytest.raises(HTTPGone):
            static_fallback(sentinel.context, sentinel.request)


class TestProxy:
    def test_it_returns_restricted_page_with_target_url(self, context, pyramid_request):
        url = context.url_from_path.return_value = "/https://example.org?a=1"

        result = proxy(context, pyramid_request)

        assert result == {"target_url": url}

    def test_it_returns_none_target_url_on_error(self, context, pyramid_request):
        context.url_from_path.side_effect = Exception("bad url")

        result = proxy(context, pyramid_request)

        assert result == {"target_url": None}

    @pytest.fixture
    def context(self):
        return create_autospec(PathURLResource, spec_set=True, instance=True)
