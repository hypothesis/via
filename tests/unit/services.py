from unittest import mock

import pytest

from via.services import (
    GoogleDriveAPI,
    HTTPService,
    PDFURLBuilder,
    SecureLinkService,
    URLDetailsService,
    ViaClientService,
    YouTubeService,
)


@pytest.fixture
def mock_service(pyramid_config):
    def mock_service(service_class):
        mock_service = mock.create_autospec(service_class, spec_set=True, instance=True)
        pyramid_config.register_service(mock_service, iface=service_class)

        return mock_service

    return mock_service


@pytest.fixture
def url_details_service(mock_service):
    return mock_service(URLDetailsService)


@pytest.fixture
def via_client_service(mock_service):
    return mock_service(ViaClientService)


@pytest.fixture
def google_drive_api(mock_service):
    return mock_service(GoogleDriveAPI)


@pytest.fixture
def secure_link_service(mock_service):
    return mock_service(SecureLinkService)


@pytest.fixture
def http_service(mock_service):
    return mock_service(HTTPService)


@pytest.fixture
def pdf_url_builder_service(mock_service):
    return mock_service(PDFURLBuilder)


@pytest.fixture
def youtube_service(mock_service):
    youtube_service = mock_service(YouTubeService)
    youtube_service.enabled = True
    youtube_service.get_video_id.return_value = None
    return youtube_service
