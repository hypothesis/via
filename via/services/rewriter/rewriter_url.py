from urllib.parse import urljoin, urlparse

from via.services.rewriter.ruleset import RewriteAction


class URLRewriter:
    def __init__(self, doc_url, rules, static_url, route_url, params):
        """
        :param static_url: The base URL for our transparent proxying
        :param route_url: The Pyramid route_url() function
        """
        self._rules = rules
        self._doc_url = doc_url
        self._doc_scheme = urlparse(doc_url).scheme

        self._static_url = static_url
        self._params = params
        self._route_url = route_url

    def can_proxy(self, url):
        # We can't really do anything with ftp:// or data://
        return url.startswith("http:") or url.startswith("https:")

    def make_absolute(self, url):
        if url.startswith("//"):
            # A special case where you don't mention the scheme and take it
            # from the parent document
            return f"{self._doc_scheme}:{url}"

        try:
            return urljoin(self._doc_url, url)
        except ValueError:
            return url

    def proxy_static(self, url):
        return self._static_url + self.make_absolute(url)

    def rewrite_css(self, url):
        return self._rewrite_end_point("view_css", url)

    def rewrite_html(self, url):
        return self._rewrite_end_point("view_html", url)

    def rewrite_js(self, url):
        return self._rewrite_end_point("view_js", url)

    ACTION_MAP = {
        RewriteAction.PROXY_STATIC: proxy_static,
        RewriteAction.MAKE_ABSOLUTE: make_absolute,
        RewriteAction.REWRITE_HTML: rewrite_html,
        RewriteAction.REWRITE_CSS: rewrite_css,
        RewriteAction.REWRITE_JS: rewrite_js,
    }

    def rewrite(self, tag, attribute, url, rel=None):
        action = self._rules.action_for(tag, attribute, url, rel)

        if action is RewriteAction.NONE:
            return None

        return self.ACTION_MAP[action](self, url)

    def _rewrite_end_point(self, endpoint, url):
        url = self.make_absolute(url)

        if self.can_proxy(url):
            params = dict(self._params)
            params["url"] = url

            return self._route_url(endpoint, _query=params)

        return url
