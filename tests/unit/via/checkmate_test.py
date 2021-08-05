from unittest.mock import create_autospec, sentinel

import pytest
from checkmatelib import CheckmateClient, CheckmateException
from checkmatelib.client import BlockResponse
from pyramid.httpexceptions import HTTPTemporaryRedirect

from via.checkmate import checkmate, raise_if_blocked


def test_it(pyramid_request):
    assert isinstance(checkmate(pyramid_request), CheckmateClient)


class TestRaiseIfBlocked:
    def test_it(self, pyramid_request):
        pyramid_request.registry.settings = {
            "checkmate_allow_all": sentinel.checkmate_allow_all,
            "checkmate_ignore_reasons": sentinel.checkmate_ignore_reasons,
        }
        pyramid_request.params["via.blocked_for"] = sentinel.via_blocked_for

        raise_if_blocked(pyramid_request, sentinel.url)

        pyramid_request.checkmate.check_url.assert_called_once_with(
            sentinel.url,
            allow_all=sentinel.checkmate_allow_all,
            blocked_for=sentinel.via_blocked_for,
            ignore_reasons=sentinel.checkmate_ignore_reasons,
        )

    def test_blocked_url(self, pyramid_request, block_response):
        pyramid_request.checkmate.check_url.return_value = block_response

        with pytest.raises(HTTPTemporaryRedirect) as exc:
            raise_if_blocked(pyramid_request, sentinel.url)

        assert exc.value.location == block_response.presentation_url

    def test_we_ignore_CheckmateExceptions(self, pyramid_request):
        pyramid_request.checkmate.check_url.side_effect = CheckmateException

        raise_if_blocked(pyramid_request, sentinel.url)

    @pytest.fixture
    def block_response(self):
        return create_autospec(BlockResponse, instance=True, spec_set=True)
