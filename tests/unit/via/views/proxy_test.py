from unittest.mock import sentinel

import pytest

from via.views.proxy import proxy


class TestProxy:
    @pytest.mark.parametrize(
        "path,url_to_proxy",
        [
            ("/https://example.com/foo", "https://example.com/foo"),
            ("/http://example.com/foo", "http://example.com/foo"),
            (
                "/https://example.com/foo?bar=gar&har=jar#car",
                "https://example.com/foo?bar=gar&har=jar#car",
            ),
        ],
    )
    def test_it(
        self, pyramid_request, path, url_to_proxy, get_url_details, via_client_service
    ):
        pyramid_request.path = path

        result = proxy(pyramid_request)

        get_url_details.assert_called_once_with(url_to_proxy)
        via_client_service.url_for.assert_called_once_with(
            url_to_proxy, sentinel.mime_type, pyramid_request.params
        )
        assert result == {"src": via_client_service.url_for.return_value}

    def test_it_normalizes_url(
        self, pyramid_request, get_url_details, via_client_service, url_from_user_input
    ):
        pyramid_request.path = "/https://example.org"
        url_from_user_input.side_effect = ["https://normalized.com"]

        proxy(pyramid_request)

        url_from_user_input.assert_called_with("https://example.org")
        get_url_details.assert_called_once_with("https://normalized.com")
        via_client_service.url_for.assert_called_once_with(
            "https://normalized.com", sentinel.mime_type, pyramid_request.params
        )

    @pytest.fixture(autouse=True)
    def get_url_details(self, patch):
        get_url_details = patch("via.views.proxy.get_url_details")
        get_url_details.return_value = (sentinel.mime_type, sentinel.status_code)
        return get_url_details

    @pytest.fixture(autouse=True)
    def url_from_user_input(self, patch):
        url_from_user_input = patch("via.views.proxy.url_from_user_input")
        url_from_user_input.side_effect = lambda url: url
        return url_from_user_input
