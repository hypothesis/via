from unittest.mock import create_autospec, sentinel

import pytest

from via.resources import PathURLResource
from via.views.proxy import proxy


class TestProxy:
    def test_it(
        self,
        context,
        pyramid_request,
        get_url_details,
        via_client_service,
        http_service,
    ):
        url = context.url_from_path.return_value = "/https://example.org?a=1"

        result = proxy(context, pyramid_request)

        pyramid_request.checkmate.raise_if_blocked.assert_called_once_with(url)
        get_url_details.assert_called_once_with(http_service, url)
        via_client_service.url_for.assert_called_once_with(
            url, sentinel.mime_type, pyramid_request.params
        )
        assert result == {"src": via_client_service.url_for.return_value}

    @pytest.fixture
    def context(self):
        return create_autospec(PathURLResource, spec_set=True, instance=True)

    @pytest.fixture(autouse=True)
    def get_url_details(self, patch):
        get_url_details = patch("via.views.proxy.get_url_details")
        get_url_details.return_value = sentinel.mime_type, sentinel.status_code
        return get_url_details
