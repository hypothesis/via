from collections import OrderedDict
from unittest.mock import sentinel

import pytest

from via.requests_tools.headers import (
    BANNED_HEADERS,
    HEADER_DEFAULTS,
    HEADER_MAP,
    add_request_headers,
    clean_headers,
)


class TestCleanHeaders:
    def test_basics(self):
        headers = {"Most-Headers": "are passed through", "Preserving": "order"}

        result = clean_headers(headers)

        assert result == headers
        assert list(result.keys()) == ["Most-Headers", "Preserving"]
        assert isinstance(result, OrderedDict)

    # For the following tests we are going to lean heavily on the defined lists
    # of headers, and just test that the function applies them correctly. Other
    # wise we just end-up copy pasting them here to no real benefit

    @pytest.mark.parametrize("header_name", BANNED_HEADERS)
    def test_we_remove_banned_headers(self, header_name):
        result = clean_headers({header_name: "value"})

        assert header_name not in result

    @pytest.mark.parametrize("header_name,default_value", HEADER_DEFAULTS.items())
    def test_we_assign_to_defaults_if_present(self, header_name, default_value):
        result = clean_headers({header_name: "some custom default"})

        assert result[header_name] == default_value

    @pytest.mark.parametrize("header_name", HEADER_DEFAULTS.keys())
    def test_we_do_not_assign_to_defaults_if_absent(self, header_name):
        result = clean_headers({})

        assert header_name not in result

    @pytest.mark.parametrize("header_name,mapped_name", HEADER_MAP.items())
    def test_we_map_mangled_header_names(self, header_name, mapped_name):
        result = clean_headers({header_name: "value"})

        assert result[mapped_name] == "value"
        assert header_name not in result


class TestAddHeaders:
    def test_it(self):
        headers = add_request_headers({"X-Existing": "existing"})

        assert headers == {
            "X-Abuse-Policy": "https://web.hypothes.is/abuse-policy/",
            "X-Complaints-To": "https://web.hypothes.is/report-abuse/",
            "X-Existing": "existing",
        }

    def test_with_request_secret_headers(self, pyramid_request, SecureSecrets):
        pyramid_request.params["via.secret.headers"] = sentinel.headers
        SecureSecrets.return_value.decrypt_dict.return_value = {
            "SECRET-HEADER": "VALUE"
        }

        headers = add_request_headers({}, request=pyramid_request)

        SecureSecrets.assert_called_once_with(
            pyramid_request.registry.settings["via_secret"].encode("utf-8")
        )
        SecureSecrets.return_value.decrypt_dict.assert_called_once_with(
            sentinel.headers
        )
        assert headers == {
            "X-Abuse-Policy": "https://web.hypothes.is/abuse-policy/",
            "X-Complaints-To": "https://web.hypothes.is/report-abuse/",
            "SECRET-HEADER": "VALUE",
        }

    @pytest.fixture
    def SecureSecrets(self, patch):
        return patch("via.requests_tools.headers.SecureSecrets")
