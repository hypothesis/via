from datetime import timedelta
from unittest.mock import create_autospec, sentinel

import pytest
from h_vialib.exceptions import TokenException
from pyramid.httpexceptions import HTTPUnauthorized

from via.services.secure_link import SecureLinkService, factory, has_secure_url_token

# pylint: disable=protected-access


class TestHasSecureURLToken:
    def test_it_with_valid_token(self, view, pyramid_request, secure_link_service):
        secure_link_service.request_is_valid.return_value = True

        result = has_secure_url_token(view)(sentinel.context, pyramid_request)

        secure_link_service.request_is_valid.assert_called_once_with(pyramid_request)
        view.assert_called_once_with(sentinel.context, pyramid_request)
        assert result == view.return_value

    def test_it_with_invalid_token(self, view, pyramid_request, secure_link_service):
        secure_link_service.request_is_valid.return_value = False

        result = has_secure_url_token(view)(sentinel.context, pyramid_request)

        assert isinstance(result, HTTPUnauthorized)

    @pytest.fixture
    def view(self):
        def view(_context, _request):
            """Emulate a view."""

        return create_autospec(view, spec_set=True)


class TestSecureLinkService:
    def test_request_is_valid(self, service, pyramid_request):
        assert service.request_is_valid(pyramid_request)

    def test_request_is_valid_can_fail(self, service, pyramid_request):
        service._via_secure_url.verify.side_effect = TokenException

        assert not service.request_is_valid(pyramid_request)

    @pytest.mark.usefixtures("with_signed_urls_not_required")
    def test_request_is_valid_if_signatures_not_required(
        self, service, pyramid_request
    ):
        assert service.request_is_valid(pyramid_request)

        service._via_secure_url.verify.assert_not_called()

    def test_sign_url(self, service):
        result = service.sign_url(sentinel.url)

        service._via_secure_url.create.assert_called_once_with(
            sentinel.url, max_age=timedelta(hours=25)
        )
        assert result == service._via_secure_url.create.return_value

    @pytest.mark.usefixtures("with_signed_urls_not_required")
    def test_sign_url_if_signatures_not_required(self, service):
        result = service.sign_url(sentinel.url)

        assert result == sentinel.url

    @pytest.fixture
    def service(self):
        return SecureLinkService(secret="not_a_secret", signed_urls_required=True)

    @pytest.fixture
    def with_signed_urls_not_required(self, service):
        service._signed_urls_required = False

    @pytest.fixture(autouse=True)
    def ViaSecureURL(self, patch):
        return patch("via.services.secure_link.ViaSecureURL")


class TestFactory:
    def test_it(self, pyramid_request, SecureLinkService):
        service = factory(sentinel.context, pyramid_request)

        SecureLinkService.assert_called_once_with(
            secret=pyramid_request.registry.settings["via_secret"],
            signed_urls_required=pyramid_request.registry.settings[
                "signed_urls_required"
            ],
        )
        assert service == SecureLinkService.return_value

    @pytest.fixture(autouse=True)
    def SecureLinkService(self, patch):
        return patch("via.services.secure_link.SecureLinkService")
