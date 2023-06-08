from unittest.mock import sentinel

import pytest

from via.services.via_client import ViaClientService, factory


class TestViaClientService:
    @pytest.mark.parametrize(
        "mime_type,expected_content_type",
        [
            ("application/x-pdf", "pdf"),
            ("application/pdf", "pdf"),
            ("text/html", "html"),
        ],
    )
    def test_content_type(self, mime_type, expected_content_type, svc):
        assert svc.content_type(mime_type) == expected_content_type

    @pytest.mark.parametrize(
        "mime_type,expected_content_type",
        [
            ("application/pdf", "pdf"),
            ("text/html", "html"),
            (None, "html"),
        ],
    )
    def test_url_for(self, mime_type, expected_content_type, svc, via_client):
        params = {"foo": "bar"}

        url = svc.url_for(sentinel.url, mime_type, params)

        via_client.url_for.assert_called_once_with(
            sentinel.url, expected_content_type, params
        )
        assert url == via_client.url_for.return_value

    @pytest.fixture
    def svc(self, via_client):
        return ViaClientService(via_client)


class TestFactory:
    def test_it(self, pyramid_request, ViaClient, ViaClientService):
        pyramid_request.registry.settings = {
            "via_html_url": sentinel.via_html_url,
            "via_secret": sentinel.via_secret,
        }

        service = factory(sentinel.context, pyramid_request)

        ViaClient.assert_called_once_with(
            service_url=pyramid_request.host_url,
            html_service_url=sentinel.via_html_url,
            secret=sentinel.via_secret,
        )
        ViaClientService.assert_called_once_with(ViaClient.return_value)
        assert service == ViaClientService.return_value

    @pytest.fixture(autouse=True)
    def ViaClientService(self, patch):
        return patch("via.services.via_client.ViaClientService")


@pytest.fixture(autouse=True)
def ViaClient(patch):
    return patch("via.services.via_client.ViaClient")


@pytest.fixture
def via_client(ViaClient):
    return ViaClient.return_value
