from collections import deque


class StreamingBuffer:
    def __init__(self, min_chunk_size):
        self._buffer = deque()
        self._chunk = ""
        self._min_chunk_size = min_chunk_size

    def add(self, data):
        self._buffer.append(data)

    def __iter__(self):
        while self._buffer:
            self._chunk += self._buffer.popleft()

            if len(self._chunk) >= self._min_chunk_size:
                yield self._chunk.encode("utf-8")
                self._chunk = ""

    def drain(self):
        yield from self
        if self._chunk:
            yield self._chunk.encode("utf-8")
