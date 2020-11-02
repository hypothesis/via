from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pyramid.testing import DummyRequest

from via.views.route_by_content._html_rewriter import HTMLRewriter


class TestHTMLRewriter:
    def test_from_request(self, pyramid_request):
        settings = {
            "legacy_via_url": sentinel.legacy_via_url,
            "via_html_url": sentinel.via_html_url,
        }
        pyramid_request.registry.settings.update(settings)

        rewriter = HTMLRewriter.from_request(pyramid_request)

        assert rewriter == Any.instance_of(HTMLRewriter).with_attrs(settings)

    def test_it_defaults_to_original_via(self):
        rewriter = HTMLRewriter(legacy_via_url=sentinel.legacy_via_url)
        assert rewriter.via_html_url == sentinel.legacy_via_url

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
            ("True", "via_html_url"),
            ("1", "via_html_url"),
            ("yes", "via_html_url"),
        ),
    )
    def test_it_switches_rewriter_based_on_rewrite_option(
        self, rewriter, enable_rewrite, expected_url
    ):
        url = rewriter.url_for({"via.rewrite": enable_rewrite, "url": "anything"})

        assert url.startswith(getattr(rewriter, expected_url))

    @pytest.mark.parametrize(
        "env_value,random_value,expected_url",
        (
            ("0.5", 0.1, "via_html_url"),
            (" 0.5  ", 0.1, "via_html_url"),
            ("0.5", 0.9, "legacy_via_url"),
            ("not_a_number", 0.1, "legacy_via_url"),
            (..., 0.5, "legacy_via_url"),
        ),
    )
    # pylint: disable=too-many-arguments
    def test_it_switches_rewriter_based_on_ratio(
        self, rewriter, os, random, env_value, random_value, expected_url
    ):
        os.environ = {}
        if env_value is not ...:
            os.environ["VIA_HTML_RATIO"] = env_value

        random.return_value = random_value

        url = rewriter.url_for({"url": "anything"})

        assert url.startswith(getattr(rewriter, expected_url))

    @pytest.fixture
    def rewriter(self):
        return HTMLRewriter(
            legacy_via_url="http://example.com/legacy_via_url",
            via_html_url="http://example.com/via_html_url",
        )

    @pytest.fixture
    def pyramid_request(self, make_request):
        return DummyRequest()

    @pytest.fixture
    def os(self, patch):
        return patch("via.views.route_by_content._html_rewriter.os")

    @pytest.fixture
    def random(self, patch):
        return patch("via.views.route_by_content._html_rewriter.random")
