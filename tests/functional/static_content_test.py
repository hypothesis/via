"""Test that content is correctly served via Whitenoise."""

import re

import pytest
from h_matchers import Any

from tests.conftest import assert_cache_control


class TestStaticContent:
    @pytest.mark.parametrize(
        "url,mime_type",  # noqa: PT006
        (  # noqa: PT007
            ("/favicon.ico", "image/x-icon"),
            ("/js/pdfjs-init.js", "text/javascript"),
        ),
    )
    def test_get_static_content(self, url, mime_type, test_app):
        response = test_app.get(url)

        assert dict(response.headers) == Any.dict().containing(
            {"Content-Type": Any.string.containing(mime_type), "ETag": Any.string()}
        )

        assert_cache_control(response.headers, ["public", "max-age=60"])

    @pytest.mark.usefixtures("checkmate_pass")
    def test_immutable_contents(self, test_app):
        salt = self.get_salt(test_app)

        response = test_app.get(f"/static/{salt}/favicon.ico")

        assert_cache_control(
            response.headers, ["max-age=315360000", "public", "immutable"]
        )

    def get_salt(self, test_app):
        """Get the salt value being used by the app.

        The most sure fire way to get the exact salt value being used is to
        actually make a call with immutable assets and then scrape the HTML
        for the salt value.
        """
        response = test_app.get("/pdf?url=http://example.com")
        static_match = re.search("/static/([^/]+)/", response.text)
        assert static_match

        return static_match.group(1)
