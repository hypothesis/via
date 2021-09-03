from unittest.mock import sentinel

import pytest

from via.views.proxy import proxy


class TestProxy:
    def test_it(self, pyramid_request, get_url_details, via_client_service):
        pyramid_request.path_qs = "/https://example.org?a=1&via.sec=HEX"

        result = proxy(pyramid_request)

        url = "https://example.org?a=1"
        pyramid_request.checkmate.raise_if_blocked.assert_called_once_with(url)
        get_url_details.assert_called_once_with(url)
        via_client_service.url_for.assert_called_once_with(
            url, sentinel.mime_type, pyramid_request.params
        )
        assert result == {"src": via_client_service.url_for.return_value}

    @pytest.fixture(autouse=True)
    def get_url_details(self, patch):
        get_url_details = patch("via.views.proxy.get_url_details")
        get_url_details.return_value = sentinel.mime_type, sentinel.status_code
        return get_url_details
