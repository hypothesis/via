from lxml import etree
from lxml.html import document_fromstring, tostring

from via.services.rewriter.img_source_set import ImageSourceSet
from via.services.rewriter.rewriter import AbstractHTMLRewriter
from via.services.timeit import timeit


class LXMLRewriter(AbstractHTMLRewriter):
    def rewrite(self, doc):
        with timeit("parse html"):
            html_doc = document_fromstring(doc.content)

        with timeit("rewriting"):
            self._rewrite_links(html_doc)

            if self.inject_client:
                self._inject_client(html_doc, doc.url)

        with timeit("stringification"):
            # TODO! - Get the original doctype
            return (b"<!DOCTYPE html>" + tostring(html_doc, encoding="utf-8")).decode(
                "utf-8"
            )

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
        base = etree.Element("base", {"href": self.url_rewriter.rewrite_html(doc_url)})
        head.insert(0, base)

        # Inject the script contents
        script_tag = etree.Element("script", attrib={"type": "text/javascript"})
        script_tag.text = self._get_client_embed()
        head.append(script_tag)

    def _rewrite_links(self, doc):
        for element, attribute, url, pos in self._iter_links(doc):
            if element.tag == "img" and attribute == "srcset":
                self._rewrite_img_srcset(element)
                continue

            replacement = self.url_rewriter.rewrite(
                element.tag, attribute, url, rel=element.get("rel")
            )
            if replacement is None:
                continue

            if attribute:
                previous = element.get(attribute)
                element.set(
                    attribute, self._update_in_place(previous, url, replacement, pos)
                )
                continue

            # If there's no attribute, this means we're being asked to rewrite
            # the content of a tag not an attribute
            element.text = self._update_in_place(element.text, url, replacement, pos)

    def _update_in_place(self, text, url, replacement, position):
        if position == 0 and text == url:
            return replacement

        end = position + len(url)
        return text[:position] + replacement + text[end:]

    def _iter_links(self, doc):
        # This yields (element, attribute, url, pos)
        yield from doc.iterlinks()

        # Lets do the same for things iterlinks doesn't find
        for img in doc.xpath("//img"):
            data_src = img.attrib.get("data-src")
            if data_src:
                yield img, "data-src", data_src, None

            src_set = img.attrib.get("srcset")
            if src_set:
                yield img, "srcset", src_set, None

    def _rewrite_img_srcset(self, img):
        src_set = img.attrib.get("srcset")
        if not src_set:
            return

        img.attrib["srcset"] = str(
            ImageSourceSet(src_set).map(
                lambda url: self.url_rewriter.rewrite("img", "srcset", url)
            )
        )
