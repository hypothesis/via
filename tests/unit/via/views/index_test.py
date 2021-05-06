import pytest
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from tests.unit.matchers import temporary_redirect_to
from via.views.exceptions import BadURL
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

    def test_post_normalizes_input(self, views, pyramid_request, url_from_user_input):
        url = pyramid_request.params["url"] = "example.com"
        url_from_user_input.side_effect = ["https://normalized.com"]

        redirect = views.post()

        url_from_user_input.assert_called_with(url)
        assert redirect == temporary_redirect_to(
            pyramid_request.route_url(route_name="proxy", url="https://normalized.com")
        )

    def test_post_url_with_query_params(self, views, pyramid_request):
        pyramid_request.params["url"] = "https://site.org?q1=value1&q2=value2"

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

    @pytest.fixture(autouse=True)
    def url_from_user_input(self, patch):
        url_from_user_input = patch("via.views.index.url_from_user_input")
        url_from_user_input.side_effect = lambda url: url
        return url_from_user_input
