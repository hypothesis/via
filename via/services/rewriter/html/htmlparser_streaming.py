from html.parser import HTMLParser
from io import StringIO

from via.services.rewriter.html.abstract import AbstractHTMLRewriter
from via.services.rewriter.html.tag_factory import TagFactory


class StreamingParser(HTMLParser):
    def __init__(self, tag_factory, inserts, buffer):
        super().__init__(convert_charrefs=False)

        self.buffer = buffer
        self.inserts = inserts
        self.tag_factory = tag_factory
        self.handle = StringIO()

    def feed(self, data):
        try:
            super().feed(data.decode("utf-8"))
        except UnicodeDecodeError:
            super().feed(data.decode("iso-8859-1"))

    def handle_starttag(self, tag, attrs):
        self.buffer.add(self.tag_factory.start(tag, dict(attrs)))

        if tag == "head":
            self.buffer.add(self.inserts.get("head_top", ""))

    def handle_endtag(self, tag):
        if tag == "head":
            self.buffer.add(self.inserts.get("head_bottom", ""))

        self.buffer.add(self.tag_factory.end(tag))

    def handle_startendtag(self, tag, attrs):
        self.buffer.add(self.tag_factory.self_closing(tag, dict(attrs)))

    def handle_data(self, data):
        # Raw content
        self.buffer.add(data)

    def handle_comment(self, data):
        self.buffer.add(f"<!-- {data} -->")

    def handle_decl(self, decl):
        self.buffer.add(f"<!{decl}>")

    def handle_pi(self, data):
        self.buffer.add(f"<{data}>")

    def unknown_decl(self, data):
        self.buffer.add(f"<![{data}]>")

    def handle_entityref(self, name):
        self.buffer.add(f"&{name};")

    def handle_charref(self, name):
        self.buffer.add(f"&#{name};")


class HTMLParserRewriter(AbstractHTMLRewriter):
    streaming = True

    def _get_streaming_parser(self, doc, buffer):
        return StreamingParser(
            tag_factory=TagFactory(self.url_rewriter),
            inserts=self.get_page_inserts(doc.url),
            buffer=buffer,
        )
