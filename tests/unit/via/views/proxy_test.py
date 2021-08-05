from unittest.mock import sentinel

import pytest

from via.views.proxy import proxy


class TestProxy:
    def test_it(
        self,
        pyramid_request,
        get_url_details,
        via_client_service,
        url_from_user_input,
        raise_if_blocked,
    ):
        pyramid_request.path = "/https://example.org"

        result = proxy(pyramid_request)

        url_from_user_input.assert_called_with("https://example.org")
        raise_if_blocked.assert_called_once_with(
            pyramid_request, url_from_user_input.return_value
        )
        get_url_details.assert_called_once_with(url_from_user_input.return_value)
        via_client_service.url_for.assert_called_once_with(
            url_from_user_input.return_value, sentinel.mime_type, pyramid_request.params
        )
        assert result == {"src": via_client_service.url_for.return_value}

    @pytest.fixture(autouse=True)
    def get_url_details(self, patch):
        get_url_details = patch("via.views.proxy.get_url_details")
        get_url_details.return_value = sentinel.mime_type, sentinel.status_code
        return get_url_details

    @pytest.fixture(autouse=True)
    def url_from_user_input(self, patch):
        return patch("via.views.proxy.url_from_user_input")

    @pytest.fixture(autouse=True)
    def raise_if_blocked(self, patch):
        return patch("via.views.proxy.raise_if_blocked")
