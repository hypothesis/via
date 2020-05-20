from urllib.parse import urljoin

from via.services.rewriter.rules import RewriteAction


class URLRewriter:
    def __init__(self, rules, static_url, route_url):
        """
        :param static_url: The base URL for our transparent proxying
        """
        self.rules = rules
        self._static_url = static_url
        self._html_url_fn = lambda url: route_url("view_html", _query={"url": url})
        self._css_url_fn = lambda url: route_url("view_css", _query={"url": url})

    def make_absolute(self, url, doc_url):
        try:
            return urljoin(doc_url, url)
        except ValueError:
            return url

    def proxy_static(self, url):
        return self._static_url + url

    def rewrite_css(self, url, doc_url):
        url = self.make_absolute(url, doc_url)

        if self.can_proxy(url):
            return self._css_url_fn(url)

        return url

    def rewrite_html(self, url, doc_url):
        url = self.make_absolute(url, doc_url)

        if self.can_proxy(url):
            return self._html_url_fn(url)

        return url

    def can_proxy(self, url):
        # We can't really do anything with ftp:// or data://
        return url.startswith("http:") or url.startswith("https:")

    def rewrite(self, tag, attribute, url, doc_url):
        action = self.rules.action_for(tag, attribute, url)

        if action is RewriteAction.NONE:
            return None

        if action is RewriteAction.PROXY_STATIC:
            return self.proxy_static(url)

        if action is RewriteAction.MAKE_ABSOLUTE:
            return self.make_absolute(url, doc_url)

        if action is RewriteAction.REWRITE_CSS:
            return self.rewrite_css(url, doc_url)

        if action is RewriteAction.REWRITE_HTML:
            return self.rewrite_html(url, doc_url)

        raise ValueError(f"Unhandled action type: {action}")
