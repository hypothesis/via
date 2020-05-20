from lxml import etree
from lxml.html import document_fromstring, tostring

from via.services.rewriter.core import HTMLRewriter
from via.services.rewriter.img_source_set import ImageSourceSet
from via.services.timeit import timeit


class LXMLRewriter(HTMLRewriter):
    def rewrite(self, doc):
        # This turns things into unicode, but it's _very_ slow
        # with timeit('unicode dance'):
        #     dammit = UnicodeDammit(content)

        with timeit("parse html"):
            html_doc = document_fromstring(doc.content)

        with timeit("rewriting"):
            self._make_links_absolute(html_doc, doc.url)
            self._rewrite_links(html_doc)

            if self.inject_client:
                self._inject_client(html_doc, doc.url)

        with timeit("stringification"):
            # TODO! - Get the original doctype
            return (b"<!DOCTYPE html>" + tostring(html_doc, encoding="utf-8")).decode(
                "utf-8"
            )

    def _make_links_absolute(self, doc, doc_url):
        doc.make_links_absolute(doc_url)

        self._rewrite_img_srcsets(doc, lambda url: self.make_url_absolute(url, doc_url))

    def _rewrite_img_srcsets(self, doc, mapping_fn):
        # LXML doesn't understand URLs in src
        for img in doc.xpath("//img"):
            src_set = img.attrib.get("srcset")
            if not src_set:
                continue

            img.attrib["srcset"] = str(ImageSourceSet(src_set).map(mapping_fn))

    def _rewrite_img_data_src(self, doc, mapping_fn):
        # LXML doesn't understand URLs in src
        for img in doc.xpath("//img"):
            data_src = img.attrib.get("data-src")
            if not data_src:
                continue

            new_value = mapping_fn(data_src)
            if new_value is None:
                continue
            img.attrib["srcset"] = new_value

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
            self._rewrite_img_srcsets(
                doc, lambda url: self.rewrite_url("img", "srcset", url)
            )

        # We always have to rewrite img data-src as they are accessed with
        # javascript
        self._rewrite_img_data_src(
            doc, lambda url: self.rewrite_url("img", "data-src", url)
        )
