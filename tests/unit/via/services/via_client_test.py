from unittest.mock import sentinel

import pytest

from via.services.via_client import factory


class TestFactory:
    def test_it(self, pyramid_request, ViaClientService):
        pyramid_request.registry.settings = {
            "via_html_url": sentinel.via_html_url,
            "via_secret": sentinel.via_secret,
        }

        service = factory(sentinel.context, pyramid_request)

        assert service == ViaClientService.return_value
        ViaClientService.assert_called_once_with(
            service_url=pyramid_request.host_url,
            html_service_url=sentinel.via_html_url,
            secret=sentinel.via_secret,
        )

    @pytest.fixture
    def ViaClientService(self, patch):
        return patch("via.services.via_client.ViaClientService")
