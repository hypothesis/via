from unittest import mock

import pytest

from via.services import ViaClientService


@pytest.fixture
def mock_service(pyramid_config):
    def mock_service(service_class):
        mock_service = mock.create_autospec(service_class, spec_set=True, instance=True)
        pyramid_config.register_service(mock_service, iface=service_class)

        return mock_service

    return mock_service


@pytest.fixture
def via_client_service(mock_service):
    return mock_service(ViaClientService)
