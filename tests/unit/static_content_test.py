"""Test that content is correctly served via Whitenoise."""

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
            {
                "Content-Type": Any.string.containing(mime_type),
                "Cache-Control": Any.string.matching(r"max-age=\d+, public"),
                "ETag": Any.string(),
            }
        )
