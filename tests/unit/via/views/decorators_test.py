from unittest import mock

import checkmatelib
import pytest
from checkmatelib import CheckmateException
from h_vialib.exceptions import TokenException
from pyramid.response import Response

from via.views.decorators import checkmate_block, has_secure_url_token


@checkmate_block
def dummy_view_checkmate_block(context, request):
    return Response("ok")


@has_secure_url_token
def dummy_view_url_token(context, request):
    return Response("ok")


class TestCheckMateBlockDecorator:
    def test_allowed_url(self, CheckmateClient, make_request):
        url = "http://example.com"
        mock_check_url = CheckmateClient.return_value.check_url
        mock_check_url.return_value = None
        request = make_request(params={"url": url})

        response = dummy_view_checkmate_block(None, request)

        mock_check_url.assert_called_once_with(
            url, allow_all=True, blocked_for=None, ignore_reasons=None
        )
        assert response.status_code == 200
        assert response.text == "ok"

    def test_blocked_url(self, CheckmateClient, make_request, block_response):
        url = "http://bad.example.com"
        mock_check_url = CheckmateClient.return_value.check_url
        mock_check_url.return_value = block_response
        request = make_request(params={"url": url})

        response = dummy_view_checkmate_block(None, request)

        mock_check_url.assert_called_once_with(
            url, allow_all=True, blocked_for=None, ignore_reasons=None
        )
        assert response.status_code == 307
        assert response.location == block_response.presentation_url

    def test_invalid_url(self, CheckmateClient, make_request):
        url = "http://bad.example.com]"
        CheckmateClient.return_value.check_url.side_effect = CheckmateException()
        request = make_request(params={"url": url})

        response = dummy_view_checkmate_block(None, request)

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
        return patch("via.views.decorators.CheckmateClient")


class TestSignedURLDecorator:
    def test_signed_urls_disabled(self, make_request, ViaSecureURL):
        request = make_request()
        request.registry.settings["signed_urls_required"] = False

        response = dummy_view_url_token(None, request)

        ViaSecureURL.assert_not_called()
        assert response.status_code == 200
        assert response.text == "ok"

    def test_signed_urls_disabled_with_signature(self, make_request, ViaSecureURL):
        request = make_request(params={"via.sec": "invalid"})
        request.registry.settings["signed_urls_required"] = False
        ViaSecureURL.return_value.verify.side_effect = TokenException()

        response = dummy_view_url_token(None, request)

        assert response.status_code == 401

    def test_invalid_token(self, make_request, ViaSecureURL):
        ViaSecureURL.return_value.verify.side_effect = TokenException()
        request = make_request(params={"via.sec": "invalid"})

        response = dummy_view_url_token(None, request)

        assert response.status_code == 401

    def test_valid_token(self, make_request, ViaSecureURL):
        ViaSecureURL.return_value.verify.return_value = "secure"
        request = make_request(params={"via.sec": "secure"})

        response = dummy_view_url_token(None, request)

        assert response.status_code == 200
        assert response.text == "ok"

    @pytest.fixture
    def ViaSecureURL(self, patch):
        return patch("via.views.decorators.ViaSecureURL")
