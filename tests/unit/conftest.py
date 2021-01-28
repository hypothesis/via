# pylint: disable=no-self-use
"""A place to put fixture functions that are useful application-wide."""
import functools
from unittest import mock
from urllib.parse import urlencode

import httpretty
import pytest
import webtest
from h_matchers import Any
from pyramid import testing
from pyramid.request import Request

from via.app import create_app
from via.views import add_routes


def autopatcher(request, target, **kwargs):
    """Patch and cleanup automatically. Wraps :py:func:`mock.patch`."""
    options = {"autospec": True}
    options.update(kwargs)
    patcher = mock.patch(target, **options)
    obj = patcher.start()
    request.addfinalizer(patcher.stop)
    return obj


@pytest.fixture
def patch(request):
    return functools.partial(autopatcher, request)


@pytest.fixture
def pyramid_config(pyramid_settings):
    with testing.testConfig(settings=pyramid_settings) as config:
        add_routes(config)
        yield config


@pytest.fixture
def pyramid_settings():
    return {
        "client_embed_url": "http://hypothes.is/embed.js",
        "nginx_server": "http://via3.hypothes.is",
        "via_html_url": "https://viahtml3.hypothes.is/proxy",
        "checkmate_url": "http://localhost:9099",
    }


@pytest.fixture
def make_request(pyramid_config):
    def make_request(path="/irrelevant", params=None):
        if params:
            path += "?" + urlencode(params)

        pyramid_request = Request.blank(path)
        pyramid_request.registry = pyramid_config.registry
        return pyramid_request

    return make_request


@pytest.fixture
def test_app(pyramid_settings):
    return webtest.TestApp(create_app(None, **pyramid_settings))


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


def assert_cache_control(headers, cache_parts):
    """Assert that all parts of the Cache-Control header are present."""
    assert dict(headers) == Any.dict.containing({"Cache-Control": Any.string()})
    assert (
        headers["Cache-Control"].split(", ") == Any.list.containing(cache_parts).only()
    )
