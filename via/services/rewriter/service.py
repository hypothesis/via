from pkg_resources import resource_filename

from via.configuration import Configuration
from via.services.rewriter.rewriter import NullRewriter
from via.services.rewriter.rewriter_css import CSSRewriter
from via.services.rewriter.rewriter_html_htmlparser import HTMLParserRewriter
from via.services.rewriter.rewriter_html_lxml import LXMLRewriter
from via.services.rewriter.rewriter_js import JSRewriter
from via.services.rewriter.rewriter_url import URLRewriter
from via.services.rewriter.ruleset import Ruleset


class RewriterService:
    HTML_REWRITERS = {
        "htmlparser": HTMLParserRewriter,
        "lxml": LXMLRewriter,
        "null": NullRewriter,
        None: LXMLRewriter,
    }

    def __init__(self, context, request):
        self._context = context
        self._request = request

    def get_js_rewriter(self, document_url):
        return JSRewriter(self._get_url_rewriter(document_url))

    def get_css_rewriter(self, document_url):
        return CSSRewriter(self._get_url_rewriter(document_url))

    def get_html_rewriter(self, document_url):
        via_config, h_config = Configuration.extract_from_params(self._request.params)

        url_rewriter = self._get_url_rewriter(document_url)

        return self.HTML_REWRITERS.get(via_config.get("rewriter"))(
            url_rewriter, h_config=h_config,
        )

    def _get_url_rewriter(self, document_url):
        ruleset = Ruleset.from_yaml(
            resource_filename("via.services.rewriter", "rules.yaml")
        )

        return URLRewriter(
            rules=ruleset,
            doc_url=document_url,
            static_url=self._context.static_proxy_url_for(""),
            route_url=self._request.route_url,
            params=self._request.params,
        )
