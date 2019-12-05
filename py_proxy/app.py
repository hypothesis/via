"""The main application entrypoint module."""
import pyramid.config


def settings():
    """Return the app's configuration settings as a dict.

    Settings are read from environment variables and fall back to hardcoded
    defaults if those variables aren't defined.

    """
    result = {}
    return result


def app():
    """Configure and return the WSGI app."""
    config = pyramid.config.Configurator(settings=settings())
    config.include("pyramid_jinja2")
    config.include("py_proxy.views")
    return config.make_wsgi_app()
