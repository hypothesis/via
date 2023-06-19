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
    def test_it(
        self, context, pyramid_request, url_details_service, via_client_service
    ):
        url_details_service.get_url_details.return_value = (
            sentinel.mime_type,
            sentinel.status_code,
        )
        url = context.url_from_path.return_value = "/https://example.org?a=1"

        result = proxy(context, pyramid_request)

        pyramid_request.checkmate.raise_if_blocked.assert_called_once_with(url)
        url_details_service.get_url_details.assert_called_once_with(url)
        via_client_service.url_for.assert_called_once_with(
            url, sentinel.mime_type, pyramid_request.params
        )
        assert result == {"src": via_client_service.url_for.return_value}

    @pytest.fixture
    def context(self):
        return create_autospec(PathURLResource, spec_set=True, instance=True)
