from unittest.mock import create_autospec

import pytest
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound, HTTPNotFound

from tests.unit.matchers import temporary_redirect_to
from via.resources import QueryURLResource
from via.views.index import IndexViews


class TestIndexGet:
    def test_it_returns_restricted_page_when_not_lms(
        self, context, pyramid_request, secure_link_service
    ):
        secure_link_service.request_has_valid_token.return_value = False
        views = IndexViews(context, pyramid_request)

        result = views.get()

        assert result == {"target_url": None}
        assert (
            pyramid_request.override_renderer == "via:templates/restricted.html.jinja2"
        )

    def test_it_returns_page_when_lms(
        self, context, pyramid_request, secure_link_service
    ):
        secure_link_service.request_has_valid_token.return_value = True
        views = IndexViews(context, pyramid_request)

        result = views.get()

        assert result == {}

    def test_it_returns_not_found_when_front_page_disabled(
        self, context, pyramid_request, secure_link_service
    ):
        secure_link_service.request_has_valid_token.return_value = True
        pyramid_request.registry.settings["enable_front_page"] = False
        views = IndexViews(context, pyramid_request)

        result = views.get()

        assert isinstance(result, HTTPNotFound)

    @pytest.fixture
    def context(self):
        return create_autospec(QueryURLResource, spec_set=True, instance=True)


class TestIndexPost:
    def test_it_returns_restricted_page_when_not_lms(
        self, context, pyramid_request, secure_link_service
    ):
        secure_link_service.request_has_valid_token.return_value = False
        views = IndexViews(context, pyramid_request)

        result = views.post()

        assert result == {"target_url": None}

    def test_it_returns_not_found_when_front_page_disabled(
        self, context, pyramid_request, secure_link_service
    ):
        secure_link_service.request_has_valid_token.return_value = True
        pyramid_request.registry.settings["enable_front_page"] = False
        views = IndexViews(context, pyramid_request)

        result = views.post()

        assert isinstance(result, HTTPNotFound)

    def test_it_redirects_when_lms(self, context, pyramid_request, secure_link_service):
        secure_link_service.request_has_valid_token.return_value = True
        context.url_from_query.return_value = "http://example.com/page?q=1"
        views = IndexViews(context, pyramid_request)

        result = views.post()

        assert isinstance(result, HTTPFound)
        assert result == temporary_redirect_to(
            pyramid_request.route_url(
                route_name="proxy",
                url="http://example.com/page",
                _query="q=1",
            )
        )

    def test_it_redirects_to_index_on_bad_url(
        self, context, pyramid_request, secure_link_service
    ):
        secure_link_service.request_has_valid_token.return_value = True
        context.url_from_query.side_effect = HTTPBadRequest("bad url")
        views = IndexViews(context, pyramid_request)

        result = views.post()

        assert isinstance(result, HTTPFound)

    @pytest.fixture
    def context(self):
        return create_autospec(QueryURLResource, spec_set=True, instance=True)
