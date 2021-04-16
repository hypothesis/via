import pytest

from tests.unit.matchers import temporary_redirect_to
from via.views.index import IndexViews


class TestIndexViews:
    def test_get(self, views):
        assert views.get() == {}

    def test_post(self, views, pyramid_request):
        url = pyramid_request.params["url"] = "https://example.com"

        redirect = views.post()

        assert redirect == temporary_redirect_to(
            pyramid_request.route_url(route_name="proxy", url=url)
        )

    def test_post_with_no_url(self, views, pyramid_request):
        assert "url" not in pyramid_request.params

        redirect = views.post()

        assert redirect == temporary_redirect_to(
            pyramid_request.route_url(route_name="index")
        )

    @pytest.fixture
    def views(self, pyramid_request):
        return IndexViews(pyramid_request)
