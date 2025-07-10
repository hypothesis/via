from os import environ

import pytest
import responses
from h_matchers import Any
from pytest_factoryboy import register

from tests.factories import TranscriptFactory, TranscriptInfoFactory, VideoFactory

# Each factory has to be registered with pytest_factoryboy.
register(TranscriptFactory)
register(TranscriptInfoFactory)
register(VideoFactory)


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
        "data_directory": "tests/data_directory",
        "dev": False,
        "youtube_transcripts": True,
        "api_jwt_secret": "secret",
        "youtube_api_key": "test_youtube_api_key",
        "database_url": environ["DATABASE_URL"],
    }


def assert_cache_control(headers, cache_parts):
    """Assert that all parts of the Cache-Control header are present."""
    assert dict(headers) == Any.dict().containing({"Cache-Control": Any.string()})
    assert (
        headers["Cache-Control"].split(", ")
        == Any.list().containing(cache_parts).only()
    )


@pytest.fixture(autouse=True)
def responses_():
    """Mock HTTP requests made using the `requests` library."""
    with responses.RequestsMock() as rsps:
        yield rsps
