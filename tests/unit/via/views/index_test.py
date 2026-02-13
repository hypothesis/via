from unittest.mock import create_autospec

import pytest

from via.resources import QueryURLResource
from via.views.index import index


class TestIndex:
    def test_it_returns_restricted_page(self, context, pyramid_request):
        result = index(context, pyramid_request)

        assert result == {"target_url": None}

    @pytest.fixture
    def context(self):
        return create_autospec(QueryURLResource, spec_set=True, instance=True)
