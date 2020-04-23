import os
import re
from contextlib import contextmanager
from datetime import datetime
from io import StringIO, BytesIO
from urllib.parse import urljoin

import requests
from bs4 import UnicodeDammit
from jinja2 import Environment, PackageLoader, select_autoescape
from lxml import etree
from lxml.html import fromstring, tostring, document_fromstring
from pyramid import view
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response

from via.configuration import Configuration


@contextmanager
def timeit(message):
    start = datetime.utcnow()
    yield
    diff = datetime.utcnow() - start
    diff = diff.seconds * 1000 + diff.microseconds / 1000

    print(f"{diff}ms {message}")


class ImageSourceSet:
    def __init__(self, raw):
        self.raw = raw
        self._parts = list(self._parse(raw))

    def map(self, url_function):
        self._parts = [
            (url_function(url) or url, size) for url, size in self._parts
        ]
        return self

    def __str__(self):
        return ', '.join(
            f"{url} {size}" for url, size in self._parts
        )

    @classmethod
    def _parse(self, raw):
        for part in raw.split(','):
            print(part)
            try:
                url, size = part.strip().split(' ', 1)
            except ValueError:
                url, size = part, ''
            yield url, size


class Rewriter:
    def __init__(self, static_url, route_url):
        """
        :param static_url: The base URL for our transparent proxying
        """
        self._static_url = static_url
        self._html_url_fn = lambda url: route_url("view_html", _query={"url": url})
        self._css_url_fn = lambda url: route_url("view_css", _query={"url": url})

    def rewrite(self, content, url):
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


class CSSRewriter(Rewriter):
    URL_REGEX = re.compile(r'url\(([^)]+)\)', re.IGNORECASE)

    def rewrite(self, content, doc_url):
        content = content.decode('utf-8')

        replacements = []

        for match in self.URL_REGEX.finditer(content):
            url = match.group(1)

            if url.startswith('"') or url.startswith("'"):
                print("HMMMM QUOTED", url)
                continue

            if url.startswith('/'):
                new_url = self.make_url_absolute(url, doc_url)

                replacements.append(
                    (match.group(0), f"url({new_url})")
                )

        for find, replace in replacements:
            content = content.replace(find, replace)

        return content


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

        if not self.rewrite_images and tag == "img" and not attribute == 'data-src':
            return False

        if not self.rewrite_forms and tag == "form":
            return False

        return True

    def rewrite_url(self, tag, attribute, url):
        if not self.is_rewritable(tag, attribute, url):
            return None

        if tag == "a" and attribute == "href":
            return self._html_url_fn(url)

        if self.rewrite_out_of_page_css and tag == "link" and attribute == "href" and url.endswith('css'):
            return self._css_url_fn(url)

        return self._static_url + url


class LXMLRewriter(HTMLRewriter):
    def rewrite(self, content, url):
        # This turns things into unicode, but it's _very_ slow
        # with timeit('unicode dance'):
        #     dammit = UnicodeDammit(content)

        with timeit("parse html"):
            doc = document_fromstring(content)

        with timeit("rewriting"):
            self._make_links_absolute(doc, url)
            self._rewrite_links(doc)

            if self.inject_client:
                self._inject_client(doc, url)

        with timeit("stringification"):
            # TODO! - Get the original doctype
            return b'<!DOCTYPE html>' + tostring(doc, encoding='utf-8')

    def _make_links_absolute(self, doc, doc_url):
        doc.make_links_absolute(doc_url)

        self._rewrite_img_srcsets(doc, lambda url: self.make_url_absolute(url, doc_url))

    def _rewrite_img_srcsets(self, doc, mapping_fn):
        # LXML doesn't understand URLs in src
        for img in doc.xpath('//img'):
            src_set = img.attrib.get('srcset')
            if not src_set:
                continue

            img.attrib['srcset'] = str(ImageSourceSet(src_set).map(mapping_fn))

    def _rewrite_img_data_src(self, doc, mapping_fn):
        # LXML doesn't understand URLs in src
        for img in doc.xpath('//img'):
            data_src = img.attrib.get('data-src')
            if not data_src:
                continue

            new_value = mapping_fn(data_src)
            if new_value is None:
                continue
            img.attrib['srcset'] = new_value

    def _inject_client(self, doc, doc_url):
        head = doc.find("head")
        if head is None:
            # We should probably add one in this case
            raise ValueError("No head to inject into!")

        # Let H know where the real document is
        canonical_link = etree.Element(
            "link", attrib={"rel": "canonical", "href": doc_url}
        )
        head.insert(0, canonical_link)

        # Also set the base to try and catch relative links that escape us
        base = etree.Element("base", {"href": self._html_url_fn(doc_url)})
        head.insert(0, base)

        # Inject the script contents
        script_tag = etree.Element("script", attrib={"type": "text/javascript"})
        script_tag.text = self._get_client_embed()
        head.append(script_tag)

    count = 0

    def _rewrite_links(self, doc):
        for element, attribute, url, pos in doc.iterlinks():
            replacement = self.rewrite_url(element.tag, attribute, url)
            if replacement is None:
                continue

            self.count += 1


            if attribute:
                element.set(attribute, replacement)
                continue

            end = pos + len(url)
            element.text = element.text[:pos] + replacement + element.text[end:]

        # LXML doesn't understand image srcsets
        if self.rewrite_images:
            self._rewrite_img_srcsets(doc, lambda url: self.rewrite_url('img', 'srcset', url))

        # We always have to rewrite img data-src as they are accessed with
        # javascript
        self._rewrite_img_data_src(doc, lambda url: self.rewrite_url('img', 'data-src', url))

@view.view_config(
    route_name="view_css", http_cache=3600,
)
def view_css(context, request):
    user_agent = request.headers.get("User-Agent")
    document_url = context.url()

    with timeit("retrieve content"):
        result = requests.get(document_url, headers={"User-Agent": user_agent})

    content_type = result.headers["Content-Type"]
    if "text/css" not in content_type.lower():
        raise HTTPNotFound("No CSS found")

    rewriter = CSSRewriter(
        static_url=context.static_proxy_url_for(""),
        route_url=request.route_url
    )

    with timeit("rewriting total"):
        body = rewriter.rewrite(result.content, document_url)

    return Response(body=body, content_type=result.headers["Content-Type"])


@view.view_config(
    route_name="view_html", http_cache=3600,
)
def view_pdf(context, request):
    user_agent = request.headers.get("User-Agent")
    document_url = context.url()

    print("REWRITE HTML", document_url)

    with timeit("retrieve content"):
        result = requests.get(
            document_url,
            # Pass the user agent
            headers={"User-Agent": user_agent},
            # Pass any cookies through
            cookies=request.cookies
        )

    content_type = result.headers["Content-Type"]
    if "text/html" not in content_type.lower():
        raise HTTPNotFound("No HTML found")

    #print("HTML Content Type", content_type, result.headers['Content-Encoding'])
    via_config, h_config = Configuration.extract_from_params(request.params)

    rewriter = LXMLRewriter(
        static_url=context.static_proxy_url_for(""),
        route_url=request.route_url,
        h_config=h_config,
    )

    with timeit("rewriting total"):
        body = rewriter.rewrite(result.content, document_url)

    response = Response(
        body=body.decode('utf-8'),
        content_type=content_type,
    )

    for key, value in result.cookies.items():
        raise ValueError('COOKOIIE')

    return response
