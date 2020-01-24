# pylint: disable=no-self-use
"""A place to put fixture functions that are useful application-wide."""
import functools
from unittest import mock

import httpretty
import pytest
from pyramid import testing
from pyramid.request import Request
from webtest import TestApp as WebTestApp  # No pytest, this isn't a test class

from py_proxy.app import create_app
from py_proxy.views import add_routes


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
        "legacy_via_url": "http://via.hypothes.is",
    }


@pytest.fixture
def make_pyramid_request(pyramid_config):
    def _make_pyramid_request(path):
        pyramid_request = Request.blank(path)
        pyramid_request.registry = pyramid_config.registry
        return pyramid_request

    return _make_pyramid_request


@pytest.fixture
def test_app(pyramid_settings):
    return WebTestApp(create_app(None, **pyramid_settings))


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
