"""The main application entrypoint module."""
import os

import pyramid.config
from pkg_resources import resource_filename
from whitenoise import WhiteNoise

from via.cache_buster import PathCacheBuster
from via.sentry_filters import SENTRY_FILTERS

REQUIRED_PARAMS = ["client_embed_url", "nginx_server", "legacy_via_url"]


def load_settings(settings):
    """Load application settings from a dict or environment variables.

    Checks that the required parameters are either filled out in the provided
    dict, or that the required values can be loaded from the environment.

    :param settings: Settings dict
    :raise ValueError: If a required parameter is not filled
    :return: A dict of settings
    """
    for param in REQUIRED_PARAMS:
        value = settings[param] = settings.get(param, os.environ.get(param.upper()))

        if value is None:
            raise ValueError(f"Param {param} must be provided.")

    # Configure sentry
    settings["h_pyramid_sentry.filters"] = SENTRY_FILTERS

    return settings


def create_app(_=None, **settings):
    """Configure and return the WSGI app."""
    config = pyramid.config.Configurator(settings=load_settings(settings))

    config.include("pyramid_jinja2")
    config.include("via.views")
    config.include("h_pyramid_sentry")

    # Configure Pyramid so we can generate static URLs
    static_path = resource_filename("via", "static")
    cache_buster = PathCacheBuster(static_path)
    print(f"Cache buster salt: {cache_buster.salt}")

    config.add_static_view(name="static", path="via:static")
    config.add_cache_buster("via:static", cachebust=cache_buster)

    app = WhiteNoise(
        config.make_wsgi_app(),
        index_file=True,
        # Config for serving files at / which are marked as mutable. This must
        # be first to allow these files to be found
        root=resource_filename("via", "static"),
        prefix="/",
        # The test to see whether files are immutable (i.e. in the second set)
        immutable_file_test=cache_buster.get_immutable_file_test(),
    )

    # Config for serving files at immutable/<salt>/path which are marked
    # as immutable
    app.add_files(
        root=static_path, prefix=cache_buster.immutable_path,
    )

    return app
