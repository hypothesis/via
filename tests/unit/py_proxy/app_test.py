from unittest import mock

import pytest

from py_proxy.app import app, load_settings
from py_proxy.sentry_filters import SENTRY_FILTERS


def test_settings_raise_value_error_if_environment_variable_is_not_set():
    with pytest.raises(ValueError):
        load_settings({})


def test_settings_are_configured_from_environment_variables(os_env):
    expected_settings = {
        "client_embed_url": "https://hypothes.is/embed.js",
        "nginx_server": "https://via3.hypothes.is",
        "legacy_via_url": "https://via.hypothes.is",
    }

    pyramid_settings = load_settings({})

    for key, value in expected_settings.items():
        assert pyramid_settings[key] == value


def test_app(configurator, pyramid, os_env):
    app()

    pyramid.config.Configurator.assert_called_once_with(
        settings={
            "client_embed_url": "https://hypothes.is/embed.js",
            "nginx_server": "https://via3.hypothes.is",
            "legacy_via_url": "https://via.hypothes.is",
            "h_pyramid_sentry.filters": SENTRY_FILTERS,
        }
    )
    assert configurator.include.call_args_list == [
        mock.call("pyramid_jinja2"),
        mock.call("py_proxy.views"),
        mock.call("h_pyramid_sentry"),
    ]
    configurator.make_wsgi_app.assert_called_once_with()


@pytest.fixture
def configurator(pyramid):
    return pyramid.config.Configurator.return_value


@pytest.fixture(autouse=True)
def pyramid(patch):
    return patch("py_proxy.app.pyramid")


@pytest.fixture
def os_env(patch):
    def get(env_var):
        env = {
            "CLIENT_EMBED_URL": "https://hypothes.is/embed.js",
            "NGINX_SERVER": "https://via3.hypothes.is",
            "LEGACY_VIA_URL": "https://via.hypothes.is",
        }
        return env[env_var]

    os = patch("py_proxy.app.os")
    os.environ.get = get
    return os
