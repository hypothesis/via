from html import escape
from html.parser import HTMLParser
from io import StringIO

from via.services.rewriter.rewriter import AbstractHTMLRewriter
from via.services.timeit import timeit


class Attribute:
    OF_INTEREST = {
        "a": {"href", "src"},
        "link": {"href"},
        "img": {"src", "srcset", "data-src"},
        "form": {"action"},
        "iframe": {"src"},
    }

    @classmethod
    def is_interesting(self, tag, attr):
        attrs = self.OF_INTEREST.get(tag)
        if not attrs:
            return False

        return attr in attrs


class StreamingParser(HTMLParser):
    def __init__(self, url_rewriter, inserts):
        super().__init__(convert_charrefs=False)

        self.url_rewriter = url_rewriter
        self.inserts = inserts
        self.handle = StringIO()
        self.current_tag = None

    @property
    def content(self):
        return self.handle.getvalue()

    def _format_attrs(self, tag, attrs):
        if not attrs:
            return ""

        parts = []
        for key, value in attrs:
            if value is None:
                parts.append(key)
            else:
                if Attribute.is_interesting(tag, key):
                    value = self._map_attr(tag, key, value)

                parts.append(f'{key}="{escape(value)}"')

        return " " + " ".join(parts)

    def _map_attr(self, tag, attr, value):
        new_value = self.url_rewriter.rewrite(tag, attr, value)
        if new_value:
            return new_value

        return value

    def _write(self, data):
        self.handle.write(data)

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        self._write(f"<{tag}{self._format_attrs(tag, attrs)}>")

        if tag == "head":
            self._write(self.inserts.get("head_top", ""))

    def handle_endtag(self, tag):
        self.current_tag = None

        if tag == "body":
            self._write(self.inserts.get("head_bottom", ""))

        self._write(f"</{tag}>")

    def handle_startendtag(self, tag, attrs):
        self._write(f"<{tag}{self._format_attrs(tag, attrs)} />")

    def handle_data(self, data):
        # Raw content
        self._write(data)

    def handle_comment(self, data):
        self._write(f"<!-- {data} -->")

    def handle_decl(self, decl):
        self._write(f"<!{decl}>")

    def handle_pi(self, data):
        self._write(f"<{data}>")

    def unknown_decl(self, data):
        self._write(f"<![{data}]>")

    def handle_entityref(self, name):
        self._write(f"&{name};")

    def handle_charref(self, name):
        self._write(f"&#{name};")


class HTMLParserRewriter(AbstractHTMLRewriter):
    def rewrite(self, doc):
        parser = StreamingParser(self.url_rewriter, self._get_inserts(doc.url))

        with timeit("parse html"):
            parser.feed(doc.content.decode("utf-8"))
            parser.close()

        return parser.content

    def _get_inserts(self, doc_url):
        if not self.inject_client:
            return {}

        base_url = self.url_rewriter.rewrite_html(doc_url)
        embed = self._get_client_embed()

        return {
            "head_top": f'\n<link rel="canonical" href="{escape(doc_url)}">\n<base href="{escape(base_url)}">\n',
            "head_bottom": f'\n<script type="text/javascript">{embed}</script>\n',
        }
