from urllib.parse import urljoin

from via.services.rewriter.rules import RewriteAction


class URLRewriter:
    def __init__(self, doc_url, rules, static_url, route_url):
        """
        :param static_url: The base URL for our transparent proxying
        :param route_url: The Pyramid route_url() function
        """
        self.rules = rules
        self.doc_url = doc_url
        self._static_url = static_url
        self._html_url_fn = lambda url: route_url("view_html", _query={"url": url})
        self._css_url_fn = lambda url: route_url("view_css", _query={"url": url})

    def can_proxy(self, url):
        # We can't really do anything with ftp:// or data://
        return url.startswith("http:") or url.startswith("https:")

    def make_absolute(self, url):
        try:
            return urljoin(self.doc_url, url)
        except ValueError:
            return url

    def proxy_static(self, url):
        return self._static_url + url

    def rewrite_css(self, url):
        url = self.make_absolute(url)

        if self.can_proxy(url):
            return self._css_url_fn(url)

        return url

    def rewrite_html(self, url):
        url = self.make_absolute(url)

        if self.can_proxy(url):
            return self._html_url_fn(url)

        return url

    ACTION_MAP = {
        RewriteAction.PROXY_STATIC: proxy_static,
        RewriteAction.REWRITE_HTML: rewrite_html,
        RewriteAction.REWRITE_CSS: rewrite_css,
        RewriteAction.MAKE_ABSOLUTE: make_absolute,
    }

    def rewrite(self, tag, attribute, url):
        action = self.rules.action_for(tag, attribute, url)

        if action is RewriteAction.NONE:
            return None

        return self.ACTION_MAP[action](self, url)
