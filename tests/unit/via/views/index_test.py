import pytest
from pyramid.httpexceptions import HTTPNotFound

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

    @pytest.mark.usefixtures("disable_front_page")
    @pytest.mark.parametrize("view", ["get", "post"])
    def test_it_404s_if_the_front_page_isnt_enabled(self, view, views, pyramid_request):
        view = getattr(views, view)

        response = view()

        assert isinstance(response, HTTPNotFound)

    @pytest.fixture
    def disable_front_page(self, pyramid_settings):
        pyramid_settings["enable_front_page"] = False

    @pytest.fixture
    def views(self, pyramid_request):
        return IndexViews(pyramid_request)
