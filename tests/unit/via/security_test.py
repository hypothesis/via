from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pyramid.security import Allowed, Denied

from via.security import ViaSecurityPolicy


class TestViaSecurityPolicy:
    def test_permits_when_theres_no_authorization_header(self, pyramid_request):
        result = ViaSecurityPolicy().permits(pyramid_request, sentinel.context, "api")

        assert result == Any.instance_of(Denied).with_attrs(
            {"msg": "No Authorization header"}
        )

    def test_permits_when_the_jwt_is_invalid(self, pyramid_request):
        pyramid_request.headers["Authorization"] = "Bearer invalid_token"
        result = ViaSecurityPolicy().permits(pyramid_request, sentinel.context, "api")

        assert result == Any.instance_of(Denied).with_attrs({"msg": "Invalid JWT"})

    @pytest.mark.usefixtures("with_valid_authorization_header")
    def test_permits_when_the_permission_is_unknown(self, pyramid_request):
        result = ViaSecurityPolicy().permits(
            pyramid_request, sentinel.context, "unknown_permission"
        )

        assert result == Any.instance_of(Denied).with_attrs(
            {"msg": "Unknown permission"}
        )

    @pytest.mark.usefixtures("with_valid_authorization_header")
    def test_permits_when_the_jwt_and_permission_are_valid(self, pyramid_request):
        result = ViaSecurityPolicy().permits(pyramid_request, sentinel.context, "api")

        assert result == Any.instance_of(Allowed).with_attrs(
            {"msg": "Valid JWT provided"}
        )

    @pytest.fixture
    def with_valid_authorization_header(self, pyramid_request):
        pyramid_request.headers["Authorization"] = (
            f"Bearer {ViaSecurityPolicy.encode_jwt(pyramid_request)}"
        )
