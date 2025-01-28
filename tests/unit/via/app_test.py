from pathlib import Path
from unittest import mock

import pytest

from via.app import configure_jinja2_assets, load_settings


class TestConfigureJinja2Assets:
    def test_it_adds_the_static_asset_url_generator_functions_to_the_template_env(
        self, pyramid_config
    ):
        assets_env = pyramid_config.registry["assets_env"] = mock.Mock(
            spec_set=["url", "urls"]
        )

        configure_jinja2_assets(pyramid_config)

        assert (
            pyramid_config.get_jinja2_environment().globals["asset_url"]
            == assets_env.url
        )
        assert (
            pyramid_config.get_jinja2_environment().globals["asset_urls"]
            == assets_env.urls
        )


def test_settings_raise_value_error_if_environment_variable_is_not_set():
    with pytest.raises(ValueError):  # noqa: PT011
        load_settings({})


@pytest.mark.usefixtures("os")
def test_settings_are_configured_from_environment_variables(pyramid_settings):
    expected_settings = pyramid_settings
    expected_settings["data_directory"] = Path(pyramid_settings["data_directory"])

    settings = load_settings({})

    for key, value in expected_settings.items():
        assert settings[key] == value


@pytest.fixture
def os(patch, pyramid_settings):
    return patch(
        "via.app.os",
        environ={key.upper(): value for key, value in pyramid_settings.items()},
    )
