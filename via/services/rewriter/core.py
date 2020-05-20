import os
from urllib.parse import urljoin

from jinja2 import Environment, PackageLoader, select_autoescape


class Rewriter:
    def __init__(self, static_url, route_url):
        """
        :param static_url: The base URL for our transparent proxying
        """
        self._static_url = static_url
        self._html_url_fn = lambda url: route_url("view_html", _query={"url": url})
        self._css_url_fn = lambda url: route_url("view_css", _query={"url": url})

    def rewrite(self, doc):
        raise NotImplementedError()

    def is_rewritable(self, url):
        if url[:5] != "http:" and url[:6] != "https:":
            return False

        _, ext = url.rsplit(".", 1)
        if ext in self.excluded_extensions:
            return False

        return True

    def make_url_absolute(self, url, doc_url):
        try:
            return urljoin(doc_url, url)
        except ValueError:
            return url


class HTMLRewriter(Rewriter):
    # Things our children do
    inject_client = True

    # Things we do
    rewrite_html_links = True
    rewrite_images = True
    rewrite_image_links = False
    rewrite_forms = False
    rewrite_out_of_page_css = True

    images = {"png", "jpg", "jpeg", "gif", "svg"}
    fonts = {"woff", "woff2", "ttf"}

    # We must statically rewrite CSS so relative links work
    excluded_extensions = images | fonts

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

    def is_rewritable(self, tag, attribute, url):
        if not super().is_rewritable(url):
            return False

        if not self.rewrite_html_links and attribute == "href" and tag in ["link", "a"]:
            print("NOT REWRIRR HTML LINKS")
            return False

        if not self.rewrite_images and tag == "img" and not attribute == "data-src":
            return False

        if not self.rewrite_forms and tag == "form":
            return False

        return True

    def rewrite_url(self, tag, attribute, url):
        if not self.is_rewritable(tag, attribute, url):
            return None

        if tag == "a" and attribute == "href":
            return self._html_url_fn(url)

        if (
            self.rewrite_out_of_page_css
            and tag == "link"
            and attribute == "href"
            and url.endswith("css")
        ):
            return self._css_url_fn(url)

        return self._static_url + url
