import os

from jinja2 import Environment, PackageLoader, select_autoescape

from via.services.rewriter.rewriter_url import URLRewriter
from via.services.rewriter.rules import RewriteRules


class AbstractRewriter:
    def __init__(self, doc_url, static_url, route_url):
        """
        :param static_url: The base URL for our transparent proxying
        """
        self.url_rewriter = URLRewriter(doc_url, RewriteRules, static_url, route_url)

    def rewrite(self, doc):
        raise NotImplementedError()


class AbstractHTMLRewriter(AbstractRewriter):
    # Things our children do
    inject_client = True

    def __init__(self, doc_url, static_url, route_url, h_config):
        """
        :param static_url: The base URL for our transparent proxying
        """
        super().__init__(doc_url, static_url, route_url)

        self._h_config = h_config
        self._jinja_env = Environment(
            loader=PackageLoader("via", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def _get_client_embed(self):
        template = self._jinja_env.get_template("client_inject.js.jinja2")

        return template.render(
            h_embed_url=os.environ.get("H_EMBED_URL", "https://hypothes.is/embed.js"),
            hypothesis_config=self._h_config,
        )
