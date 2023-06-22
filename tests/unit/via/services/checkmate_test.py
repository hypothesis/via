from unittest.mock import create_autospec, sentinel

import pytest
from checkmatelib import BadURL as CheckmateBadURL
from checkmatelib import CheckmateException
from checkmatelib.client import BlockResponse
from pyramid.httpexceptions import HTTPTemporaryRedirect

from via.exceptions import BadURL
from via.services.checkmate import CheckmateService, factory


class TestCheckmateService:
    def test_check_url(self, checkmate_client, svc):
        result = svc.check_url(sentinel.url)

        checkmate_client.check_url.assert_called_once_with(
            sentinel.url,
            allow_all=sentinel.allow_all,
            blocked_for=sentinel.blocked_for,
            ignore_reasons=sentinel.ignore_reasons,
        )
        assert result == checkmate_client.check_url.return_value

    @pytest.mark.parametrize("exception_class", [CheckmateBadURL, CheckmateException])
    def test_check_url_raises_if_CheckmateClient_raises(
        self, checkmate_client, svc, exception_class
    ):
        checkmate_client.check_url.side_effect = exception_class

        with pytest.raises(exception_class):
            svc.check_url(sentinel.url)

    def test_raise_if_blocked_doesnt_raise_if_not_blocked(self, checkmate_client, svc):
        checkmate_client.check_url.return_value = None

        svc.raise_if_blocked(sentinel.url)

        checkmate_client.check_url.assert_called_once_with(
            sentinel.url,
            allow_all=sentinel.allow_all,
            blocked_for=sentinel.blocked_for,
            ignore_reasons=sentinel.ignore_reasons,
        )

    def test_raise_if_blocked_raises_if_the_given_url_is_blocked(
        self, checkmate_client, svc, block_response
    ):
        checkmate_client.check_url.return_value = block_response

        with pytest.raises(HTTPTemporaryRedirect) as exc_info:
            svc.raise_if_blocked(sentinel.url)

        assert exc_info.value.location == block_response.presentation_url

    def test_raise_if_blocked_raises_if_the_given_url_is_bad(
        self, checkmate_client, svc
    ):
        checkmate_client.check_url.side_effect = CheckmateBadURL()

        with pytest.raises(BadURL) as exc_info:
            svc.raise_if_blocked(sentinel.url)

        assert exc_info.value.args[0] == checkmate_client.check_url.side_effect
        assert exc_info.value.url == sentinel.url

    def test_raise_if_blocked_doesnt_raise_if_checkmate_crashes(
        self, checkmate_client, svc
    ):
        checkmate_client.check_url.side_effect = CheckmateException

        svc.raise_if_blocked(sentinel.url)

    @pytest.fixture
    def block_response(self):
        return create_autospec(BlockResponse, instance=True, spec_set=True)

    @pytest.fixture
    def checkmate_client(self, CheckmateClient):
        return CheckmateClient.return_value

    @pytest.fixture
    def svc(self, checkmate_client):
        return CheckmateService(
            checkmate_client=checkmate_client,
            allow_all=sentinel.allow_all,
            blocked_for=sentinel.blocked_for,
            ignore_reasons=sentinel.ignore_reasons,
        )


class TestFactory:
    def test_it(self, pyramid_request, CheckmateClient, CheckmateService):
        svc = factory(sentinel.context, pyramid_request)

        CheckmateClient.assert_called_once_with(
            host=sentinel.url, api_key=sentinel.api_key
        )
        CheckmateService.assert_called_once_with(
            checkmate_client=CheckmateClient.return_value,
            allow_all=sentinel.allow_all,
            blocked_for=None,
            ignore_reasons=sentinel.ignore_reasons,
        )
        assert svc == CheckmateService.return_value

    def test_it_passes_the_via_blocked_for_query_param_to_CheckmateService(
        self, pyramid_request, CheckmateService
    ):
        pyramid_request.params["via.blocked_for"] = sentinel.blocked_for

        factory(sentinel.context, pyramid_request)

        assert CheckmateService.call_args[1]["blocked_for"] == sentinel.blocked_for

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.registry.settings["checkmate_url"] = sentinel.url
        pyramid_request.registry.settings["checkmate_api_key"] = sentinel.api_key
        pyramid_request.registry.settings["checkmate_allow_all"] = sentinel.allow_all
        pyramid_request.registry.settings[
            "checkmate_ignore_reasons"
        ] = sentinel.ignore_reasons
        return pyramid_request

    @pytest.fixture(autouse=True)
    def CheckmateService(self, patch):
        return patch("via.services.checkmate.CheckmateService")


@pytest.fixture(autouse=True)
def CheckmateClient(patch):
    return patch("via.services.checkmate.CheckmateClient")
