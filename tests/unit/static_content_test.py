"""Test that content is correctly served via Whitenoise."""

import re

import pytest
from h_matchers import Any

# pylint: disable=no-value-for-parameter
# Pylint doesn't seem to understand h_matchers here for some reason


class TestStaticContent:
    @pytest.mark.parametrize(
        "url,mime_type",
        (
            ("/robots.txt", "text/plain"),
            ("/favicon.ico", "image/x-icon"),
            ("/", "text/html"),
            ("/js/pdfjs-init.js", "application/javascript"),
        ),
    )
    def test_get_static_content(self, url, mime_type, test_app):
        response = test_app.get(url)

        assert dict(response.headers) == Any.dict.containing(
            {"Content-Type": Any.string.containing(mime_type), "ETag": Any.string()}
        )

        self.cache_assertion(response.headers, ["public", "max-age=60"])

    def test_immutable_contents(self, test_app):
        salt = self.get_salt(test_app)

        response = test_app.get(f"/static/{salt}/robots.txt")

        self.cache_assertion(
            response.headers, ["max-age=315360000", "public", "immutable"]
        )

    def get_salt(self, test_app):
        response = test_app.get(f"/pdf/http://example.com")
        static_match = re.search("/static/([^/]+)/", response.text)
        assert static_match

        return static_match.group(1)

    def cache_assertion(self, headers, cache_parts):
        assert dict(headers) == Any.dict.containing({"Cache-Control": Any.string()})

        assert (
            headers["Cache-Control"].split(", ")
            == Any.list.containing(cache_parts).only()
        )
