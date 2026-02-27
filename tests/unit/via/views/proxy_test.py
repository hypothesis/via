from unittest.mock import create_autospec, sentinel

import pytest
from pyramid.httpexceptions import HTTPGone

from via.resources import PathURLResource
from via.views.proxy import proxy, static_fallback


class TestStaticFallback:
    def test_it(self):
        with pytest.raises(HTTPGone):
            static_fallback(sentinel.context, sentinel.request)


class TestProxy:
    def test_it_returns_restricted_page_when_not_lms(
        self, context, pyramid_request, secure_link_service
    ):
        secure_link_service.request_has_valid_token.return_value = False
        url = context.url_from_path.return_value = "/https://example.org?a=1"

        result = proxy(context, pyramid_request)

        assert result == {"target_url": url}
        assert (
            pyramid_request.override_renderer == "via:templates/restricted.html.jinja2"
        )

    def test_it_returns_restricted_none_url_on_error_when_not_lms(
        self, context, pyramid_request, secure_link_service
    ):
        secure_link_service.request_has_valid_token.return_value = False
        context.url_from_path.side_effect = Exception("bad url")

        result = proxy(context, pyramid_request)

        assert result == {"target_url": None}

    def test_it_proxies_when_lms(
        self,
        context,
        pyramid_request,
        secure_link_service,
        url_details_service,
        via_client_service,  # noqa: ARG002
    ):
        secure_link_service.request_has_valid_token.return_value = True
        context.url_from_path.return_value = "http://example.com/page"
        url_details_service.get_url_details.return_value = ("text/html", 200)

        result = proxy(context, pyramid_request)

        url_details_service.get_url_details.assert_called_once_with(
            "http://example.com/page"
        )
        assert "src" in result

    @pytest.fixture
    def context(self):
        return create_autospec(PathURLResource, spec_set=True, instance=True)
