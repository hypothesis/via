from unittest import mock

import checkmatelib
import pytest
from checkmatelib import CheckmateException
from pyramid.response import Response

from via.views.blocker import checkmate_block


@checkmate_block
def dummy_view(context, request):
    return Response("ok")


class TestCheckMateBlockDecorator:
    def test_allowed_url(self, CheckmateClient, make_request):
        url = "http://example.com"
        mock_check_url = CheckmateClient.return_value.check_url
        mock_check_url.return_value = None
        request = make_request(params={"url": url})

        response = dummy_view(None, request)

        mock_check_url.assert_called_once_with(url, allow_all=True)
        assert response.status_code == 200
        assert response.text == "ok"

    def test_blocked_url_disabled_checkmate(self, CheckmateClient, make_request):
        url = "http://bad.example.com"
        mock_check_url = CheckmateClient.return_value.check_url
        request = make_request(params={"url": url})
        request.registry.settings["checkmate_enabled"] = False

        response = dummy_view(None, request)

        mock_check_url.assert_not_called()

        assert response.status_code == 200
        assert response.text == "ok"

    def test_blocked_url(self, CheckmateClient, make_request, block_response):
        url = "http://bad.example.com"
        mock_check_url = CheckmateClient.return_value.check_url
        mock_check_url.return_value = block_response
        request = make_request(params={"url": url})

        response = dummy_view(None, request)

        mock_check_url.assert_called_once_with(url, allow_all=True)
        assert response.status_code == 307
        assert response.location == block_response.presentation_url

    def test_invalid_url(self, CheckmateClient, make_request):
        url = "http://bad.example.com]"
        CheckmateClient.return_value.check_url.side_effect = CheckmateException()
        request = make_request(params={"url": url})

        response = dummy_view(None, request)

        # Request continues despite Checkmate errors
        assert response.status_code == 200
        assert response.text == "ok"

    @pytest.fixture
    def block_response(self):
        return mock.create_autospec(
            checkmatelib.client.BlockResponse, instance=True, spec_set=True
        )

    @pytest.fixture
    def CheckmateClient(self, patch):
        return patch("via.views.blocker.CheckmateClient")
