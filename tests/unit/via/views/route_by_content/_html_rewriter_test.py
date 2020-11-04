from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pyramid.testing import DummyRequest

from via.views.route_by_content._html_rewriter import HTMLRewriter

# pylint: disable=protected-access


class TestHTMLRewriter:
    def test_from_request(self, pyramid_request):
        settings = {
            "via_html_url": sentinel.via_html_url,
        }
        pyramid_request.registry.settings.update(settings)

        rewriter = HTMLRewriter.from_request(pyramid_request)

        assert rewriter == Any.instance_of(HTMLRewriter).with_attrs(
            {"_via_html_url": sentinel.via_html_url}
        )

    def test_it_extracts_the_url_and_prepends_it(self, rewriter):
        doc_url = "http://example.com/doc"

        url = rewriter.url_for({"url": doc_url})

        assert url.startswith(f"{rewriter._via_html_url}/{doc_url}")

    def test_it_merges_params(self, rewriter):
        doc_url = "http://example.com/doc?a=1&b=2"

        url = rewriter.url_for({"url": doc_url, "via.openSidebar": "1", "other": "any"})

        assert url == Any.url.with_query(
            {
                "a": "1",
                "b": "2",
                "via.openSidebar": "1",
                # Currently we merge any old stuff in, perhaps we shouldn't?
                "other": "any",
            }
        )

    @pytest.fixture
    def rewriter(self):
        return HTMLRewriter(
            via_html_url="http://example.com/via_html_url",
        )

    @pytest.fixture
    def pyramid_request(self, make_request):
        return DummyRequest()
