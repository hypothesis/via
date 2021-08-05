import pytest
from h_vialib.exceptions import TokenException
from pyramid.response import Response

from via.views.decorators import has_secure_url_token


@has_secure_url_token
def dummy_view_url_token(context, request):
    return Response("ok")


class TestSignedURLDecorator:
    def test_signed_urls_disabled(self, pyramid_request, ViaSecureURL):
        pyramid_request.registry.settings["signed_urls_required"] = False

        response = dummy_view_url_token(None, pyramid_request)

        ViaSecureURL.assert_not_called()
        assert response.status_code == 200
        assert response.text == "ok"

    def test_signed_urls_disabled_with_signature(self, pyramid_request, ViaSecureURL):
        pyramid_request.params["via.sec"] = "invalid"
        pyramid_request.registry.settings["signed_urls_required"] = False
        ViaSecureURL.return_value.verify.side_effect = TokenException()

        response = dummy_view_url_token(None, pyramid_request)

        assert response.status_code == 401

    def test_invalid_token(self, pyramid_request, ViaSecureURL):
        ViaSecureURL.return_value.verify.side_effect = TokenException()
        pyramid_request.params["via.sec"] = "invalid"

        response = dummy_view_url_token(None, pyramid_request)

        assert response.status_code == 401

    def test_valid_token(self, pyramid_request, ViaSecureURL):
        ViaSecureURL.return_value.verify.return_value = "secure"
        pyramid_request.params["via.sec"] = "secure"

        response = dummy_view_url_token(None, pyramid_request)

        assert response.status_code == 200
        assert response.text == "ok"

    @pytest.fixture
    def ViaSecureURL(self, patch):
        return patch("via.views.decorators.ViaSecureURL")
