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

        We use the proxy route to scrape for the salt since the PDF viewer
        is now restricted. Any page that includes static assets will work.
        """
        # Use a URL that will hit the proxy route and return the restricted page
        response = test_app.get("/https://example.com")
        static_match = re.search("/static/([^/]+)/", response.text)
        if not static_match:
            # The restricted template doesn't reference /static/ paths,
            # so read the salt directly from stdout capture during app startup.
            # Fall back to getting it from the cache buster.
            import importlib_resources

            from via.cache_buster import PathCacheBuster

            static_path = str(importlib_resources.files("via") / "static")
            cache_buster = PathCacheBuster(static_path)
            return cache_buster.salt

        return static_match.group(1)
