from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pyramid.testing import DummyRequest

from via.views.route_by_content._html_rewriter import HTMLRewriter


class TestHTMLRewriter:
    def test_from_request(self, pyramid_request):
        settings = {
            "legacy_via_url": sentinel.legacy_via_url,
            "internal_rewriter_url": sentinel.internal_rewriter_url,
        }
        pyramid_request.registry.settings.update(settings)

        rewriter = HTMLRewriter.from_request(pyramid_request)

        assert rewriter == Any.instance_of(HTMLRewriter).with_attrs(settings)

    def test_it_defaults_to_original_via(self):
        rewriter = HTMLRewriter(legacy_via_url=sentinel.legacy_via_url)
        assert rewriter.internal_rewriter_url == sentinel.legacy_via_url

    def test_it_extracts_the_url_and_prepends_it(self, rewriter):
        doc_url = "http://example.com/doc"

        url = rewriter.url_for({"url": doc_url})

        assert url.startswith(f"{rewriter.legacy_via_url}/{doc_url}")

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

    @pytest.mark.parametrize(
        "enable_rewrite,expected_url",
        (
            ("False", "legacy_via_url"),
            ("", "legacy_via_url"),
            ("0", "legacy_via_url"),
            ("True", "internal_rewriter_url"),
            ("1", "internal_rewriter_url"),
            ("yes", "internal_rewriter_url"),
        ),
    )
    def test_it_switches_rewriter_based_on_rewrite_option(
        self, rewriter, enable_rewrite, expected_url
    ):
        url = rewriter.url_for({"via.rewrite": enable_rewrite, "url": "anything"})

        assert url.startswith(getattr(rewriter, expected_url))

    @pytest.fixture
    def rewriter(self):
        return HTMLRewriter(
            legacy_via_url="http://example.com/legacy_via_url",
            internal_rewriter_url="http://example.com/internal_rewriter_url",
        )


@pytest.fixture
def pyramid_request(make_request):
    return DummyRequest()
