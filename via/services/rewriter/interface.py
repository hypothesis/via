from via.services.rewriter.streaming import StreamingBuffer
from via.services.timeit import timeit


class AbstractRewriter:
    streaming = False
    chunk_size_in = 65536
    chunk_size_out = 16384

    def __init__(self, url_rewriter):
        self.url_rewriter = url_rewriter

    def rewrite(self, doc):
        raise NotImplementedError()

    def streaming_rewrite(self, doc):
        buffer = StreamingBuffer(self.chunk_size_out)

        parser = self._get_streaming_parser(doc, buffer)

        with timeit("streaming rewrite time"):
            for chunk in doc.original.iter_content(chunk_size=self.chunk_size_in):
                parser.feed(chunk)

                yield from buffer

            parser.close()

            yield from buffer.drain()

    def _get_streaming_parser(self, doc, buffer):
        raise NotImplementedError()
