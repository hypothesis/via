from via.configuration import Configuration
from via.services.rewriter.css import CSSRewriter
from via.services.rewriter.html import HTML_REWRITERS
from via.services.rewriter.js import JSRewriter
from via.services.rewriter.ruleset import Rules
from via.services.rewriter.url import URLRewriter


class RewriterService:
    DEFAULT_REWRITER = "htmlparser"

    def __init__(self, context, request):
        self._context = context
        self._request = request

    def get_js_rewriter(self, document_url):
        return JSRewriter(self._get_url_rewriter(document_url, Rules.js()))

    def get_css_rewriter(self, document_url):
        return CSSRewriter(self._get_url_rewriter(document_url, Rules.css()))

    def get_html_rewriter(self, document_url):
        via_config, h_config = Configuration.extract_from_params(self._request.params)

        url_rewriter = self._get_url_rewriter(document_url, Rules.html())

        rewriter = HTML_REWRITERS.get(
            via_config.get("rewriter", self.DEFAULT_REWRITER)
        )(url_rewriter, h_config=h_config, static_url=self._request.static_url)

        chunk_size_in = via_config.get("csi")
        if chunk_size_in:
            rewriter.chunk_size_in = int(chunk_size_in)

        chunk_size_out = via_config.get("cso")
        if chunk_size_out:
            rewriter.chunk_size_out = int(chunk_size_out)

        return rewriter

    def _get_url_rewriter(self, document_url, ruleset):
        return URLRewriter(
            rules=ruleset,
            doc_url=document_url,
            static_url=self._context.static_proxy_url_for(""),
            route_url=self._request.route_url,
            params=self._request.params,
        )
