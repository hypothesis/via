from unittest import mock

import pytest

from via.app import create_app, load_settings
from via.sentry_filters import SENTRY_FILTERS


def test_settings_raise_value_error_if_environment_variable_is_not_set():
    with pytest.raises(ValueError):
        load_settings({})


def test_settings_are_configured_from_environment_variables(os_env, pyramid_settings):
    expected_settings = pyramid_settings

    settings = load_settings({})

    for key, value in expected_settings.items():
        assert settings[key] == value


def test_app(configurator, pyramid, os_env, pyramid_settings):
    create_app()

    expected_settings = dict(
        {"h_pyramid_sentry.filters": SENTRY_FILTERS}, **pyramid_settings
    )

    pyramid.config.Configurator.assert_called_once_with(settings=expected_settings)
    assert configurator.include.call_args_list == [
        mock.call("pyramid_jinja2"),
        mock.call("via.views"),
        mock.call("h_pyramid_sentry"),
    ]
    configurator.make_wsgi_app.assert_called_once_with()


@pytest.fixture
def configurator(pyramid):
    return pyramid.config.Configurator.return_value


@pytest.fixture(autouse=True)
def pyramid(patch):
    return patch("via.app.pyramid")


@pytest.fixture
def os_env(patch, pyramid_settings):
    def get(env_var):
        return pyramid_settings[env_var.lower()]

    os = patch("via.app.os")
    os.environ.get = get
    return os
