from unittest.mock import create_autospec

import pytest
from h_vialib import ContentType
from pyramid.httpexceptions import HTTPFound

from via.resources import QueryURLResource
from via.views.route_by_content import route_by_content


class TestRouteByContent:
    def test_it_returns_restricted_page_when_not_lms(
        self, context, pyramid_request, secure_link_service
    ):
        secure_link_service.request_has_valid_token.return_value = False

        result = route_by_content(context, pyramid_request)

        assert result == {"target_url": context.url_from_query.return_value}
        assert (
            pyramid_request.override_renderer == "via:templates/restricted.html.jinja2"
        )

    def test_it_returns_restricted_none_url_on_error_when_not_lms(
        self, context, pyramid_request, secure_link_service
    ):
        secure_link_service.request_has_valid_token.return_value = False
        context.url_from_query.side_effect = Exception("bad url")

        result = route_by_content(context, pyramid_request)

        assert result == {"target_url": None}

    def test_it_routes_when_lms(
        self,
        context,
        pyramid_request,
        secure_link_service,
        url_details_service,
        via_client_service,
    ):
        secure_link_service.request_has_valid_token.return_value = True
        context.url_from_query.return_value = "http://example.com/doc.pdf"
        pyramid_request.params["url"] = "http://example.com/doc.pdf"
        url_details_service.get_url_details.return_value = ("application/pdf", 200)
        via_client_svc = via_client_service
        via_client_svc.url_for.return_value = "http://via/routed"

        result = route_by_content(context, pyramid_request)

        assert isinstance(result, HTTPFound)

    def test_it_uses_caching_headers_for_pdf(
        self,
        context,
        pyramid_request,
        secure_link_service,
        url_details_service,
        via_client_service,
    ):
        secure_link_service.request_has_valid_token.return_value = True
        context.url_from_query.return_value = "http://example.com/doc.pdf"
        pyramid_request.params["url"] = "http://example.com/doc.pdf"
        url_details_service.get_url_details.return_value = ("application/pdf", 200)
        via_client_service.content_type.return_value = ContentType.PDF
        via_client_service.url_for.return_value = "http://via/routed"

        result = route_by_content(context, pyramid_request)

        assert isinstance(result, HTTPFound)
        assert "max-age=300" in result.headers["Cache-Control"]

    def test_it_returns_no_cache_for_server_errors(
        self,
        context,
        pyramid_request,
        secure_link_service,
        url_details_service,
        via_client_service,
    ):
        secure_link_service.request_has_valid_token.return_value = True
        context.url_from_query.return_value = "http://example.com/page"
        pyramid_request.params["url"] = "http://example.com/page"
        url_details_service.get_url_details.return_value = ("text/html", 500)
        via_client_service.content_type.return_value = ContentType.HTML
        via_client_service.url_for.return_value = "http://via/routed"

        result = route_by_content(context, pyramid_request)

        assert isinstance(result, HTTPFound)
        assert result.headers["Cache-Control"] == "no-cache"

    def test_it_returns_short_cache_for_404(
        self,
        context,
        pyramid_request,
        secure_link_service,
        url_details_service,
        via_client_service,
    ):
        secure_link_service.request_has_valid_token.return_value = True
        context.url_from_query.return_value = "http://example.com/page"
        pyramid_request.params["url"] = "http://example.com/page"
        url_details_service.get_url_details.return_value = ("text/html", 404)
        via_client_service.content_type.return_value = ContentType.HTML
        via_client_service.url_for.return_value = "http://via/routed"

        result = route_by_content(context, pyramid_request)

        assert isinstance(result, HTTPFound)
        assert "max-age=60" in result.headers["Cache-Control"]

    @pytest.fixture
    def context(self):
        return create_autospec(QueryURLResource, spec_set=True, instance=True)
