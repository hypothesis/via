# pylint: disable=no-self-use
"""A place to put fixture functions that are useful application-wide."""
import functools
from urllib.parse import urlencode

from pyramid import testing
from pyramid.request import Request, apply_request_extensions

from tests.unit.services import *  # pylint: disable=wildcard-import,unused-wildcard-import
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
        config.include("pyramid_services")
        add_routes(config)
        yield config


@pytest.fixture
def make_request(pyramid_config):
    def make_request(path="/irrelevant", params=None):
        if params:
            path += "?" + urlencode(params)

        pyramid_request = Request.blank(path)
        pyramid_request.registry = pyramid_config.registry
        apply_request_extensions(pyramid_request)

        return pyramid_request

    return make_request
