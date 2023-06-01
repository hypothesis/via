import httpretty
import pytest
import webtest

from via.app import create_app


@pytest.fixture
def test_app(pyramid_settings):
    return webtest.TestApp(create_app(None, **pyramid_settings))


@pytest.fixture
def checkmate_pass():
    httpretty.register_uri(
        httpretty.GET, "http://localhost:9099/api/check", status=204, body=""
    )
