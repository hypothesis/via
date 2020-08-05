from lxml.html import HTMLParser
from lxml.html.html5parser import HTMLParser as HTMLParser5

from via.services.rewriter.html.abstract import AbstractHTMLRewriter
from via.services.rewriter.html.tag_factory import TagFactory


class ParserCallback:
    def __init__(self, tag_factory, inserts, buffer):
        self.buffer = buffer
        self._tag_factory = tag_factory
        self._inserts = inserts

    def start(self, tag, attrib):
        self.buffer.add(self._tag_factory.start(tag, attrib))

        if tag == "head":
            self.buffer.add(self._inserts.get("head_top", ""))

    def end(self, tag):
        if tag == "head":
            self.buffer.add(self._inserts.get("head_bottom", ""))

        if not self._tag_factory.is_self_closing(tag):
            self.buffer.add(self._tag_factory.end(tag))

    def data(self, data):
        self.buffer.add(data)

    def comment(self, text):
        self.buffer.add(f"<!-- {text} -->")

    def doctype(self, doc_type, public, dtd):
        doc_type = f"<!DOCTYPE {doc_type}"

        if public:
            doc_type += f' PUBLIC "{public}"'

        if dtd:
            doc_type += f' "{dtd}"'

        doc_type += ">\n"

        self.buffer.add(doc_type)

    def pi(self, *args, **kwargs):
        raise NotImplementedError(f"pi {args}, {kwargs}")

    def start_ns(self, *args, **kwargs):
        raise NotImplementedError(f"start_ns {args}, {kwargs}")

    def end_ns(self, *args, **kwargs):
        raise NotImplementedError(f"end_ns {args}, {kwargs}")

    def close(self):
        pass


class LXMLStreamingRewriter(AbstractHTMLRewriter):
    streaming = True

    def _get_streaming_parser(self, doc, buffer):
        return HTMLParser(
            collect_ids=False,
            target=ParserCallback(
                tag_factory=TagFactory(self.url_rewriter),
                inserts=self.get_page_inserts(doc.url),
                buffer=buffer,
            ),
        )
