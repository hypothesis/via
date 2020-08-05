import re

from via.services.rewriter.html.abstract import AbstractHTMLRewriter


class NullRewriter(AbstractHTMLRewriter):
    HEAD_TAG_OPEN = re.compile(r"(<\s*head[^>]*>)", re.IGNORECASE)
    HEAD_TAG_CLOSE = re.compile(r"(<\s*/\s*head\s*>)", re.IGNORECASE)

    def rewrite(self, doc):
        content = doc.content.decode("iso-8859-1")
        content = self._do_injects(content, doc.url)

        return content

    def _do_injects(self, content, doc_url):
        injects = self.get_page_inserts(doc_url)

        head_top = injects.get("head_top")
        if head_top:
            content = self.HEAD_TAG_OPEN.sub(f"\\1{head_top}", content, count=1)

        head_bottom = injects.get("head_bottom")
        if head_bottom:
            content = self.HEAD_TAG_CLOSE.sub(f"{head_bottom}\\1", content, count=1)

        return content


class NullParser:
    def __init__(self, buffer):
        self.buffer = buffer

    def feed(self, data):
        # The encoding isn't right, but it works, and this is only for
        # speed testing
        self.buffer.add(data.decode("iso-8859-1"))

    def close(self):
        pass


class NullStreamingRewriter(AbstractHTMLRewriter):
    streaming = True

    def _get_streaming_parser(self, doc, buffer):
        return NullParser(buffer)
