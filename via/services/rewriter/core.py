import os
import re
from urllib.parse import urljoin

from jinja2 import Environment, PackageLoader, select_autoescape

from via.services.rewriter.rules import RewriteRules, RewriteAction


class Rewriter:
    rules = RewriteRules

    def __init__(self, static_url, route_url):
        """
        :param static_url: The base URL for our transparent proxying
        """
        self._static_url = static_url
        self._html_url_fn = lambda url: route_url("view_html", _query={"url": url})
        self._css_url_fn = lambda url: route_url("view_css", _query={"url": url})

    def rewrite(self, doc):
        raise NotImplementedError()

    def make_url_absolute(self, url, doc_url):
        try:
            return urljoin(doc_url, url)
        except ValueError:
            return url

    def rewrite_url(self, tag, attribute, url, doc_url):
        action = self.rules.action_for(tag, attribute, url)

        if action is RewriteAction.NONE:
            return None

        if action is RewriteAction.PROXY_STATIC:
            return self._static_url + url

        url = self.make_url_absolute(url, doc_url)

        if action is RewriteAction.MAKE_ABSOLUTE:
            return url

        if action is RewriteAction.REWRITE_CSS:
            return self._css_url_fn(url)

        if action is RewriteAction.REWRITE_HTML:
            return self._html_url_fn(url)

        raise ValueError(f"Unhandled action type: {action}")


class HTMLRewriter(Rewriter):
    # Things our children do
    inject_client = True

    def __init__(self, static_url, route_url, h_config):
        """
        :param static_url: The base URL for our transparent proxying
        """
        super().__init__(static_url, route_url)

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


class CSSRewriter(Rewriter):
    URL_REGEX = re.compile(r"url\(([^)]+)\)", re.IGNORECASE)

    def rewrite(self, doc):
        content = doc.content.decode("utf-8")

        replacements = []

        for match in self.URL_REGEX.finditer(content):
            url = match.group(1)

            if url.startswith('"') or url.startswith("'"):
                continue

            if url.startswith("/"):
                new_url = self.make_url_absolute(url, doc.url)

                replacements.append((match.group(0), f"url({new_url})"))

        for find, replace in replacements:
            content = content.replace(find, replace)

        return content
