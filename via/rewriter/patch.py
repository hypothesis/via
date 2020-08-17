"""Tools to apply the hooks to a running `pywb` app."""

from pywb.apps.rewriterapp import RewriterApp
from pywb.rewrite.default_rewriter import DefaultRewriter
from pywb.rewrite.html_rewriter import HTMLRewriter
from pywb.rewrite.url_rewriter import UrlRewriter


def apply_post_app_hooks(rewriter_app, hooks):
    """Apply hooks after the app has been instantiated."""
    _PatchedRewriterApp.patch(rewriter_app, hooks)


def apply_pre_app_hooks(hooks):
    """Apply hooks before the app has been instantiated."""

    _patch_url_rewriter(hooks)
    _PatchedHTMLRewriter.patch()


def _patch_url_rewriter(hooks):
    # Modify the list of prefixes that prevent a URL from being rewritten
    prefixes = list(UrlRewriter.NO_REWRITE_URI_PREFIX)
    prefixes.extend(hooks.ignore_prefixes)
    UrlRewriter.NO_REWRITE_URI_PREFIX = tuple(prefixes)


class _PatchedHTMLRewriter(HTMLRewriter):  # pylint: disable=abstract-method
    @classmethod
    def patch(cls):
        """Patch the parent object."""

        DefaultRewriter.DEFAULT_REWRITERS["html"] = _PatchedHTMLRewriter

    def _rewrite_link_href(self, attr_value, tag_attrs, rw_mod):
        # Prevent `pywb` from attempting to insert Javascript style rewriting
        # stuff into "<link rel='manifest'>" items. This fixes a bug with
        # www.theguardian.com which declares it's manifest as `text/javascript`
        rel = self.get_attr(tag_attrs, "rel")

        if rel == "manifest":
            # 'id_' type hint appears to disable any rewriting
            return self._rewrite_url(attr_value, "id_")

        return super()._rewrite_link_href(attr_value, tag_attrs, rw_mod)


class _PatchedRewriterApp(RewriterApp):
    hooks = None

    @classmethod
    def patch(cls, rewriter, hooks):
        """Patch the rewriter object."""

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
