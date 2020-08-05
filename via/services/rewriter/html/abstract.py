import json
import os
from html import escape

from jinja2 import Environment, PackageLoader, select_autoescape

from via.services.rewriter.interface import AbstractRewriter
from via.services.rewriter.ruleset import Rules


class AbstractHTMLRewriter(AbstractRewriter):
    inject_client = True
    inject_js_rewriter = True

    def __init__(self, url_rewriter, h_config, static_url):
        """
        :param static_url: The base URL for our transparent proxying
        """
        super().__init__(url_rewriter)

        self._h_config = h_config
        self._static_url = static_url

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

    def get_page_inserts(self, doc_url):
        if not self.inject_client:
            return {}

        # base_url = self.url_rewriter.rewrite_html(doc_url)
        embed = self._get_client_embed()

        head_top = f'\n<link rel="canonical" href="{escape(doc_url)}">\n<base href="{escape(doc_url)}">\n'
        # Disable referer to attempt to fix image blocks
        head_top += '<meta name="referrer" content="no-referrer" />'

        if self.inject_js_rewriter:
            head_top += self._client_side_rewriter_inject(doc_url)

        return {
            "head_top": head_top,
            "head_bottom": f'\n<script type="text/javascript">{embed}</script>\n',
        }

    def _client_side_rewriter_inject(self, doc_url):
        settings = {
            "baseUrl": doc_url,
            "viaUrl": self.url_rewriter.rewrite_html(doc_url),
            "urlTemplates": self.url_rewriter.get_templates(),
            "ruleset": Rules.js().as_list(),
        }

        return f"""<script type="text/javascript">
            const VIA_REWRITER_SETTINGS = {json.dumps(settings)};
        </script>
        <script src="{self._static_url('via:static/js/rewriter.js')}" type="text/javascript"></script>
        """
