import pytest
import webtest

from via.app import create_app


@pytest.fixture
def test_app(pyramid_settings):
    return webtest.TestApp(create_app(None, **pyramid_settings))
