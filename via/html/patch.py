"""Tools to apply the hooks to a running `pywb` app."""

from pywb.apps.rewriterapp import RewriterApp
from pywb.rewrite.url_rewriter import UrlRewriter


def apply_hooks(rewriter_app, hooks):
    # Add most hook points
    PatchedRewriterApp.patch(rewriter_app, hooks)

    # Patch out URLs to ignore
    patch_url_rewriter(hooks)


def patch_url_rewriter(hooks):
    prefixes = list(UrlRewriter.NO_REWRITE_URI_PREFIX)
    prefixes.extend(hooks.ignore_prefixes)
    UrlRewriter.NO_REWRITE_URI_PREFIX = tuple(prefixes)


class PatchedRewriterApp(RewriterApp):
    hooks = None

    def __init__(self, framed_replay=False, jinja_env=None, config=None, paths=None):
        super().__init__(framed_replay, jinja_env, config, paths)

    @classmethod
    def patch(cls, rewriter, hooks):
        # Change the class of the rewriter to be this class, forcibly casting
        # it to be an instance of this class
        rewriter.__class__ = cls
        rewriter.hooks = hooks

        # Update the Jinja environment to have the vars we want
        rewriter.jinja_env.jinja_env.globals.update(hooks.template_vars())

        # Set the Content-Security-Policy header
        rewriter.csp_header = hooks.csp_header

    def get_upstream_url(self, wb_url, kwargs, params):
        params["url"] = self.hooks.filter_doc_url(doc_url=params["url"])

        return super().get_upstream_url(wb_url, kwargs, params)
