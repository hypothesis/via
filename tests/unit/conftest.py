# pylint: disable=no-self-use
"""A place to put fixture functions that are useful application-wide."""
import functools

from pyramid import testing
from pyramid.request import apply_request_extensions

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
def pyramid_request(
    pyramid_config,  # pylint:disable=unused-argument
):
    pyramid_request = testing.DummyRequest()
    apply_request_extensions(pyramid_request)
    return pyramid_request
