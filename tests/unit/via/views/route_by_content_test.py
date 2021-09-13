from unittest.mock import create_autospec, sentinel

import pytest

from tests.conftest import assert_cache_control
from tests.unit.matchers import temporary_redirect_to
from via.resources import URLResource
from via.views.route_by_content import route_by_content


@pytest.mark.usefixtures("via_client_service")
class TestRouteByContent:
    @pytest.mark.parametrize(
        "content_type,status_code,expected_cache_control_header",
        [
            ("PDF", 200, "public, max-age=300, stale-while-revalidate=86400"),
            ("HTML", 200, "public, max-age=60, stale-while-revalidate=86400"),
            ("HTML", 401, "public, max-age=60, stale-while-revalidate=86400"),
            ("HTML", 404, "public, max-age=60, stale-while-revalidate=86400"),
            ("HTML", 500, "no-cache"),
            ("HTML", 501, "no-cache"),
        ],
    )
    def test_it(
        self,
        content_type,
        context,
        expected_cache_control_header,
        get_url_details,
        pyramid_request,
        status_code,
        via_client_service,
    ):
        pyramid_request.params = {"url": sentinel.url, "foo": "bar"}
        get_url_details.return_value = (sentinel.mime_type, status_code)
        via_client_service.is_pdf.return_value = content_type == "PDF"

        response = route_by_content(context, pyramid_request)

        url = context.url_from_query.return_value
        pyramid_request.checkmate.raise_if_blocked.assert_called_once_with(url)
        get_url_details.assert_called_once_with(url, pyramid_request.headers)
        via_client_service.is_pdf.assert_called_once_with(sentinel.mime_type)
        via_client_service.url_for.assert_called_once_with(
            url, sentinel.mime_type, {"foo": "bar"}
        )
        assert response == temporary_redirect_to(
            via_client_service.url_for.return_value
        )
        assert_cache_control(
            response.headers, expected_cache_control_header.split(", ")
        )

    @pytest.fixture
    def context(self):
        return create_autospec(URLResource, spec_set=True, instance=True)

    @pytest.fixture(autouse=True)
    def get_url_details(self, patch):
        return patch("via.views.route_by_content.get_url_details")
