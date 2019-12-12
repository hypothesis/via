from unittest import mock

import pytest

from py_proxy.app import app, settings


def test_settings():
    assert settings() == {}


def test_app(configurator, pyramid):
    app()

    pyramid.config.Configurator.assert_called_once_with(settings={})
    assert configurator.include.call_args_list == [
        mock.call("pyramid_jinja2"),
        mock.call("py_proxy.views"),
    ]
    configurator.make_wsgi_app.assert_called_once_with()


@pytest.fixture
def configurator(pyramid):
    return pyramid.config.Configurator.return_value


@pytest.fixture(autouse=True)
def pyramid(patch):
    return patch("py_proxy.app.pyramid")
