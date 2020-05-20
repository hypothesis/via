import os

from jinja2 import Environment, PackageLoader, select_autoescape


class AbstractRewriter:
    def __init__(self, url_rewriter):
        self.url_rewriter = url_rewriter

    def rewrite(self, doc):
        raise NotImplementedError()


class AbstractHTMLRewriter(AbstractRewriter):
    # Things our children do
    inject_client = True

    def __init__(self, url_rewriter, h_config):
        """
        :param static_url: The base URL for our transparent proxying
        """
        super().__init__(url_rewriter)

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


class NullRewriter(AbstractHTMLRewriter):
    def rewrite(self, doc):
        return doc.content
