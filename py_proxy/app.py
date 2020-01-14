"""The main application entrypoint module."""
import os

import pyramid.config

from py_proxy.sentry_filters import SENTRY_FILTERS


def settings():
    """Return the app's configuration settings as a dict.

    Settings are read from environment variables and fall back to hardcoded
    defaults if those variables aren't defined.

    """
    client_embed_url = os.environ.get("CLIENT_EMBED_URL")
    nginx_server = os.environ.get("NGINX_SERVER")
    legacy_via_url = os.environ.get("LEGACY_VIA_URL")

    result = {
        "client_embed_url": client_embed_url,
        "nginx_server": nginx_server,
        "legacy_via_url": legacy_via_url,
    }
    for param in result:
        if result[param] is None:
            raise ValueError(f"Param {param} must be provided.")

    # Configure sentry
    result.update(
        {"h_pyramid_sentry.filters": SENTRY_FILTERS,}
    )

    return result


def app():
    """Configure and return the WSGI app."""
    config = pyramid.config.Configurator(settings=settings())
    config.add_static_view(name="static", path="static")
    config.include("pyramid_jinja2")
    config.include("py_proxy.views")
    config.include("h_pyramid_sentry")
    return config.make_wsgi_app()
