from unittest.mock import create_autospec, patch, sentinel

import pytest
from checkmatelib import BadURL as CheckmateBadURL
from checkmatelib import CheckmateException
from checkmatelib.client import BlockResponse
from pyramid.httpexceptions import HTTPTemporaryRedirect

from via.checkmate import ViaCheckmateClient
from via.exceptions import BadURL


class TestViaCheckmateClient:
    def test_it_initialises_correctly(self, client, pyramid_request):
        # pylint: disable=protected-access
        client._host = pyramid_request.registry.settings["checkmate_url"]
        client._api_key = pyramid_request.registry.settings["checkmate_api_key"]

    def test_raise_if_blocked(self, client, pyramid_request, check_url):
        pyramid_request.registry.settings = {
            "checkmate_allow_all": sentinel.checkmate_allow_all,
            "checkmate_ignore_reasons": sentinel.checkmate_ignore_reasons,
        }
        pyramid_request.params["via.blocked_for"] = sentinel.via_blocked_for

        client.raise_if_blocked(sentinel.url)

        check_url.assert_called_once_with(
            sentinel.url,
            allow_all=sentinel.checkmate_allow_all,
            blocked_for=sentinel.via_blocked_for,
            ignore_reasons=sentinel.checkmate_ignore_reasons,
        )

    def test_raise_if_blocked_can_block(self, client, check_url, block_response):
        check_url.return_value = block_response

        with pytest.raises(HTTPTemporaryRedirect) as exc:
            client.raise_if_blocked(sentinel.url)

        assert exc.value.location == block_response.presentation_url

    def test_raise_if_blocked_reraises_BadURL(self, client, check_url):
        check_url.side_effect = CheckmateBadURL

        with pytest.raises(BadURL) as exc:
            client.raise_if_blocked(sentinel.url)

        assert exc.value.url == sentinel.url

    def test_raise_if_blocked_ignores_CheckmateExceptions(self, client, check_url):
        check_url.side_effect = CheckmateException

        client.raise_if_blocked(sentinel.url)

    @pytest.fixture
    def client(self, pyramid_request):
        return ViaCheckmateClient(pyramid_request)

    @pytest.fixture(autouse=True)
    def check_url(self, client):
        with patch.object(client, "check_url") as check_url:
            check_url.return_value = None
            yield check_url

    @pytest.fixture
    def block_response(self):
        return create_autospec(BlockResponse, instance=True, spec_set=True)
