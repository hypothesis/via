import pytest

from via.views._helpers import url_from_user_input


class TestURLFromUserInput:
    @pytest.mark.parametrize(
        "input_url, expected",
        [
            # URLs that should be returned unchanged
            ("http://example.com", "http://example.com"),
            ("https://example.com", "https://example.com"),
            # URLs without a protocol that should have `https://` prefixed
            ("example.com", "https://example.com"),
            # Leading and trailing whitespace that should be stripped
            (" http://example.com", "http://example.com"),
            ("http://example.com ", "http://example.com"),
            # Empty URLs that should return an empty string
            ("", ""),
            ("  ", ""),
        ],
    )
    def test_it(self, input_url, expected):
        assert url_from_user_input(input_url) == expected
