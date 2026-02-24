from unittest.mock import create_autospec

import pytest
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
        assert pyramid_request.override_renderer == "via:templates/restricted.html.jinja2"

    def test_it_returns_restricted_none_url_on_error_when_not_lms(
        self, context, pyramid_request, secure_link_service
    ):
        secure_link_service.request_has_valid_token.return_value = False
        context.url_from_query.side_effect = Exception("bad url")

        result = route_by_content(context, pyramid_request)

        assert result == {"target_url": None}

    def test_it_routes_when_lms(
        self, context, pyramid_request, secure_link_service, url_details_service, via_client_service
    ):
        secure_link_service.request_has_valid_token.return_value = True
        context.url_from_query.return_value = "http://example.com/doc.pdf"
        pyramid_request.params["url"] = "http://example.com/doc.pdf"
        url_details_service.get_url_details.return_value = ("application/pdf", 200)
        via_client_svc = via_client_service
        via_client_svc.url_for.return_value = "http://via/routed"

        result = route_by_content(context, pyramid_request)

        assert isinstance(result, HTTPFound)

    @pytest.fixture
    def context(self):
        return create_autospec(QueryURLResource, spec_set=True, instance=True)
