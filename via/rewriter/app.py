"""The application providing a WSGI entry-point."""


import logging
import os

from gevent.monkey import patch_all

patch_all()  # This needs to happen before we load other classes

# pylint: disable=wrong-import-position
from pywb.apps.frontendapp import FrontEndApp

from via.rewriter.hooks import Hooks
from via.rewriter.patch import apply_post_app_hooks, apply_pre_app_hooks


class Application:
    """A collection of tools to create and configure `pywb`."""

    @classmethod
    def create(cls):
        """Create a WSGI application for proxying HTML."""

        # Move into the correct directory as template paths are relative
        os.chdir("via/rewriter")
        os.environ["PYWB_CONFIG_FILE"] = "pywb_config.yaml"

        config = cls._config_from_env()
        cls._setup_logging(config["debug"])

        # Setup hook points and apply those which must be done pre-application
        hooks = Hooks(config)
        apply_pre_app_hooks(hooks)

        app = FrontEndApp()

        # Setup hook points after the app is loaded
        apply_post_app_hooks(app.rewriterapp, hooks)

        return app

    @classmethod
    def _setup_logging(cls, debug=False):
        if debug:
            print("Enabling debug level logging")

        logging.basicConfig(
            format="%(asctime)s: [%(levelname)s]: %(message)s",
            level=logging.DEBUG if debug else logging.INFO,
        )

    @classmethod
    def _config_from_env(cls):
        """Parse options from environment variables."""

        return {
            "ignore_prefixes": cls._split_multiline(os.environ["VIA_IGNORE_PREFIXES"]),
            "h_embed_url": os.environ["VIA_H_EMBED_URL"],
            "debug": os.environ.get("VIA_DEBUG", False),
        }

    @classmethod
    def _split_multiline(cls, value):
        return [part for part in [p.strip() for p in value.split(",")] if part]


# Our job here is to leave this `application` attribute laying around as it's
# what uWSGI expects to find.
application = Application.create()  # pylint: disable=invalid-name
