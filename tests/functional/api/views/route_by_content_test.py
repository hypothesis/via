from urllib.parse import quote_plus

import httpretty
import pytest
from h_matchers import Any

from tests.conftest import assert_cache_control


class TestRouteByContent:
    DEFAULT_OPTIONS = {  # noqa: RUF012
        "via.client.ignoreOtherConfiguration": "1",
        "via.client.openSidebar": "1",
        "via.external_link_mode": "new-tab",
    }

    @pytest.mark.usefixtures("html_response", "checkmate_pass")
    def test_proxy_html(self, test_app):
        target_url = "http://example.com"

        response = test_app.get(f"/route?url={target_url}")

        assert response.status_code == 302
        query = dict(self.DEFAULT_OPTIONS)
        assert response.location == Any.url.matching(
            f"https://viahtml.hypothes.is/proxy/{target_url}/"
        ).with_query(query)

    @pytest.mark.usefixtures("pdf_response", "checkmate_pass")
    def test_proxy_pdf(self, test_app):
        target_url = "http://example.com"

        response = test_app.get(f"/route?url={target_url}")

        assert response.status_code == 302
        query = dict(self.DEFAULT_OPTIONS)
        query["via.sec"] = Any.string()
        query["url"] = target_url
        assert response.location == Any.url.matching(
            f"http://localhost/pdf?url={quote_plus(target_url)}"
        ).with_query(query)
        assert_cache_control(
            response.headers, ["public", "max-age=300", "stale-while-revalidate=86400"]
        )

    @pytest.fixture
    def html_response(self):
        httpretty.register_uri(
            httpretty.GET,
            "http://example.com",
            status=204,
            adding_headers={"Content-Type": "text/html"},
        )

    @pytest.fixture
    def pdf_response(self):
        httpretty.register_uri(
            httpretty.GET,
            "http://example.com",
            status=204,
            adding_headers={"Content-Type": "application/pdf"},
        )
