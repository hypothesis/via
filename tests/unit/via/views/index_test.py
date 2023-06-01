import pytest
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from tests.unit.matchers import temporary_redirect_to
from via.resources import QueryURLResource
from via.views.exceptions import BadURL
from via.views.index import IndexViews


class TestIndexViews:
    def test_get(self, views):
        assert views.get() == {}

    def test_post(self, views, pyramid_request):
        pyramid_request.params["url"] = "//site.org?q1=value1&q2=value2"

        redirect = views.post()

        assert isinstance(redirect, HTTPFound)
        assert (
            redirect.location
            == "http://example.com/https://site.org?q1=value1&q2=value2"
        )

    def test_post_with_no_url(self, views, pyramid_request):
        assert "url" not in pyramid_request.params

        redirect = views.post()

        assert redirect == temporary_redirect_to(
            pyramid_request.route_url(route_name="index")
        )

    def test_post_raises_if_url_invalid(self, views, pyramid_request):
        # Set a `url` that causes `urlparse` to throw.
        pyramid_request.params["url"] = "http://::12.34.56.78]/"

        with pytest.raises(BadURL):
            views.post()

    @pytest.mark.usefixtures("disable_front_page")
    @pytest.mark.parametrize("view", ["get", "post"])
    def test_it_404s_if_the_front_page_isnt_enabled(self, view, views):
        view = getattr(views, view)

        response = view()

        assert isinstance(response, HTTPNotFound)

    @pytest.fixture
    def disable_front_page(self, pyramid_settings):
        pyramid_settings["enable_front_page"] = False

    @pytest.fixture
    def views(self, context, pyramid_request):
        return IndexViews(context, pyramid_request)

    @pytest.fixture
    def context(self, pyramid_request):
        return QueryURLResource(pyramid_request)
