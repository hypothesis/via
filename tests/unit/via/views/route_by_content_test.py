from unittest.mock import create_autospec, sentinel

import pytest
from h_vialib import ContentType

from tests.conftest import assert_cache_control
from tests.unit.matchers import temporary_redirect_to
from via.resources import QueryURLResource
from via.views.route_by_content import route_by_content


@pytest.mark.usefixtures("via_client_service")
class TestRouteByContent:
    @pytest.mark.parametrize(
        "content_type,status_code,expected_cache_control_header",
        [
            (ContentType.PDF, 200, "public, max-age=300, stale-while-revalidate=86400"),
            (
                ContentType.YOUTUBE,
                200,
                "public, max-age=300, stale-while-revalidate=86400",
            ),
            (ContentType.HTML, 200, "public, max-age=60, stale-while-revalidate=86400"),
            (ContentType.HTML, 401, "public, max-age=60, stale-while-revalidate=86400"),
            (ContentType.HTML, 404, "public, max-age=60, stale-while-revalidate=86400"),
            (ContentType.HTML, 500, "no-cache"),
            (ContentType.HTML, 501, "no-cache"),
        ],
    )
    def test_it(
        self,
        content_type,
        context,
        expected_cache_control_header,
        url_details_service,
        pyramid_request,
        status_code,
        via_client_service,
        checkmate_service,
    ):
        pyramid_request.params = {"url": sentinel.url, "foo": "bar"}
        url_details_service.get_url_details.return_value = (
            sentinel.mime_type,
            status_code,
        )
        via_client_service.content_type.return_value = content_type

        response = route_by_content(context, pyramid_request)

        url = context.url_from_query.return_value
        checkmate_service.raise_if_blocked.assert_called_once_with(url)
        url_details_service.get_url_details.assert_called_once_with(
            url, pyramid_request.headers
        )
        via_client_service.content_type.assert_called_once_with(sentinel.mime_type)
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
        return create_autospec(QueryURLResource, spec_set=True, instance=True)
