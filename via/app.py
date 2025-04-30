"""The main application entrypoint module."""

import os
from pathlib import Path

import importlib_resources
import pyramid.config
from pyramid.settings import asbool
from whitenoise import WhiteNoise

from via._version import get_version
from via.cache_buster import PathCacheBuster
from via.security import ViaSecurityPolicy
from via.sentry_filters import SENTRY_FILTERS

PARAMETERS = {
    "client_embed_url": {"required": True},
    "database_url": {"required": True},
    "nginx_server": {"required": True},
    "via_html_url": {"required": True},
    "checkmate_url": {"required": True},
    "via_secret": {"required": True},
    "checkmate_api_key": {"required": True},
    "nginx_secure_link_secret": {"required": True},
    "checkmate_ignore_reasons": {},
    "checkmate_allow_all": {"formatter": asbool},
    "dev": {"formatter": asbool},
    "data_directory": {"required": True, "formatter": Path},
    "signed_urls_required": {"formatter": asbool},
    "enable_front_page": {"formatter": asbool},
    "youtube_transcripts": {"formatter": asbool},
    "api_jwt_secret": {"required": True},
    "youtube_api_key": {},
    "youtube_proxy": {},
}


def configure_jinja2_assets(config):
    jinja2_env = config.get_jinja2_environment()
    jinja2_env.globals["asset_url"] = config.registry["assets_env"].url
    jinja2_env.globals["asset_urls"] = config.registry["assets_env"].urls


def load_settings(settings):
    """Load application settings from a dict or environment variables.

    Checks that the required parameters are either filled out in the provided
    dict, or that the required values can be loaded from the environment.

    :param settings: Settings dict
    :raise ValueError: If a required parameter is not filled
    :return: A dict of settings
    """
    for param, options in PARAMETERS.items():
        formatter = options.get("formatter", lambda v: v)

        value = settings[param] = formatter(
            settings.get(param, os.environ.get(param.upper()))
        )

        if value is None and options.get("required"):
            raise ValueError(f"Param {param} must be provided.")  # noqa: EM102, TRY003

    # Configure sentry
    settings["h_pyramid_sentry.filters"] = SENTRY_FILTERS
    settings["h_pyramid_sentry.init.release"] = get_version()

    return settings


def create_app(_=None, **settings):  # pragma: no cover
    """Configure and return the WSGI app."""
    config = pyramid.config.Configurator(settings=load_settings(settings))

    config.set_security_policy(ViaSecurityPolicy())

    config.registry.settings["tm.annotate_user"] = False
    config.registry.settings["tm.manager_hook"] = "pyramid_tm.explicit_manager"
    config.include("pyramid_tm")

    config.include("pyramid_exclog")
    config.include("pyramid_jinja2")
    config.include("pyramid_services")
    config.include("h_pyramid_sentry")

    config.include("via.models")
    config.include("via.db")
    config.include("via.assets")
    config.include("via.views")
    config.include("via.services")

    # Configure Pyramid so we can generate static URLs
    static_path = str(importlib_resources.files("via") / "static")
    cache_buster = PathCacheBuster(static_path)
    print(f"Cache buster salt: {cache_buster.salt}")  # noqa: T201

    config.add_static_view(name="static", path="via:static")
    config.add_cache_buster("via:static", cachebust=cache_buster)

    config.add_tween("via.tweens.robots_tween_factory")

    # Add this as near to the end of your config as possible:
    config.include("pyramid_sanity")

    config.action(None, configure_jinja2_assets, args=(config,))

    app = WhiteNoise(
        config.make_wsgi_app(),
        index_file=True,
        # Config for serving files at static/<salt>/path which are marked
        # as immutable
        root=static_path,
        prefix=cache_buster.immutable_path,
        immutable_file_test=cache_buster.get_immutable_file_test(),
    )

    app.add_files(
        # Config for serving files at / which are marked as mutable. This is
        # for / -> index.html
        root=static_path,
        prefix="/",
    )

    return app
