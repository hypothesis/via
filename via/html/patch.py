"""Tools to apply the hooks to a running `pywb` app."""
from pywb.apps.frontendapp import FrontEndApp
from pywb.apps.rewriterapp import RewriterApp
from pywb.rewrite.url_rewriter import UrlRewriter


def apply_post_app_hooks(rewriter_app, hooks):
    # Add most hook points
    PatchedRewriterApp.patch(rewriter_app, hooks)


def apply_pre_app_hooks(hooks):
    """Apply hooks before the app has been instantiated."""

    # Patch out URLs to ignore
    patch_url_rewriter(hooks)


def patch_url_rewriter(hooks):
    # Modify the list of prefixes that prevent a URL from being rewritten
    prefixes = list(UrlRewriter.NO_REWRITE_URI_PREFIX)
    prefixes.extend(hooks.ignore_prefixes)
    UrlRewriter.NO_REWRITE_URI_PREFIX = tuple(prefixes)


class PatchedFrontEndApp(FrontEndApp):
    def handle_request(self, environ, start_response):
        # Ensure we can map in the script name from NGINX
        if "HTTP_SCRIPT_NAME" in environ:
            environ["SCRIPT_NAME"] = environ["HTTP_SCRIPT_NAME"]

        return super().handle_request(environ, start_response)


class PatchedRewriterApp(RewriterApp):
    hooks = None

    @classmethod
    def patch(cls, rewriter, hooks):
        # Change the class of the rewriter to be this class, forcibly casting
        # it to be an instance of this class
        rewriter.__class__ = cls
        rewriter.hooks = hooks

        # Update the Jinja environment to have the vars we want
        rewriter.jinja_env.jinja_env.globals.update(hooks.template_vars)

        # Set the Content-Security-Policy header
        rewriter.csp_header = hooks.csp_header

    def get_upstream_url(self, wb_url, kwargs, params):
        params["url"] = self.hooks.get_upstream_url(doc_url=params["url"])

        return super().get_upstream_url(wb_url, kwargs, params)
