import pytest

from via.app import create_app, load_settings
from via.sentry_filters import SENTRY_FILTERS


def test_settings_raise_value_error_if_environment_variable_is_not_set():
    with pytest.raises(ValueError):
        load_settings({})


def test_settings_are_configured_from_environment_variables(os, pyramid_settings):
    expected_settings = pyramid_settings

    settings = load_settings({})

    for key, value in expected_settings.items():
        assert settings[key] == value


def test_app(configurator, pyramid, os, pyramid_settings):
    create_app()

    expected_settings = dict(
        {"h_pyramid_sentry.filters": SENTRY_FILTERS}, **pyramid_settings
    )

    pyramid.config.Configurator.assert_called_once_with(settings=expected_settings)
    configurator.make_wsgi_app.assert_called_once_with()


@pytest.fixture
def configurator(pyramid):
    return pyramid.config.Configurator.return_value


@pytest.fixture(autouse=True)
def pyramid(patch):
    return patch("via.app.pyramid")


@pytest.fixture
def os(patch, pyramid_settings):
    return patch(
        "via.app.os",
        environ={key.upper(): value for key, value in pyramid_settings.items()},
    )
