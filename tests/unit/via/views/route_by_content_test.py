from unittest.mock import create_autospec

import pytest

from via.resources import QueryURLResource
from via.views.route_by_content import route_by_content


class TestRouteByContent:
    def test_it_returns_restricted_page_with_target_url(self, context, pyramid_request):
        result = route_by_content(context, pyramid_request)

        assert result == {"target_url": context.url_from_query.return_value}

    def test_it_returns_none_target_url_on_error(self, context, pyramid_request):
        context.url_from_query.side_effect = Exception("bad url")

        result = route_by_content(context, pyramid_request)

        assert result == {"target_url": None}

    @pytest.fixture
    def context(self):
        return create_autospec(QueryURLResource, spec_set=True, instance=True)
