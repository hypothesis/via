import httpretty
import pytest
from h_matchers import Any


@pytest.fixture
def pyramid_settings():
    return {
        "client_embed_url": "http://hypothes.is/embed.js",
        "nginx_server": "http://via.hypothes.is",
        "via_html_url": "https://viahtml.hypothes.is/proxy",
        "checkmate_url": "http://localhost:9099",
        "nginx_secure_link_secret": "not_a_secret",
        "via_secret": "not_a_secret",
        "signed_urls_required": False,
        "checkmate_api_key": "dev_api_key",
        "checkmate_ignore_reasons": None,
        "checkmate_allow_all": False,
        "enable_front_page": True,
        "youtube_captions": True,
        "data_directory": "tests/data_directory",
        "dev": False,
    }


def assert_cache_control(headers, cache_parts):
    """Assert that all parts of the Cache-Control header are present."""
    assert dict(headers) == Any.dict.containing({"Cache-Control": Any.string()})
    assert (
        headers["Cache-Control"].split(", ") == Any.list.containing(cache_parts).only()
    )


@pytest.fixture(autouse=True)
def httpretty_():
    """Monkey-patch Python's socket core module to mock all HTTP responses.

    We never want real HTTP requests to be sent by the tests so replace them
    all with mock responses. This handles requests sent using the standard
    urllib2 library and the third-party httplib2 and requests libraries.
    """
    httpretty.enable(allow_net_connect=False)

    yield

    httpretty.disable()
    httpretty.reset()
