from io import StringIO

from webvtt import WebVTT
from webvtt.parsers import SRTParser

from via.services.http import HTTPService


class TranscriptService:
    """Fetch transcripts in WebVTT or SRT formats."""

    def __init__(self, http_service: HTTPService):
        self._http_service = http_service

    def get_transcript(self, url: str):
        """Fetch a transcript and return it in JSON format."""

        transcript = self._get_vtt(url)
        segments = []

        for caption in transcript:
            start = caption.start_in_seconds
            end = caption.end_in_seconds
            segments.append(
                {"start": start, "duration": end - start, "text": caption.text}
            )

        return segments

    def _get_vtt(self, url: str) -> WebVTT:
        response = self._http_service.get(url)
        content = response.text.strip()
        content_buf = StringIO(content)

        # See https://www.w3.org/TR/webvtt1/#file-structure
        if content.startswith("WEBVTT"):
            return WebVTT.read_buffer(content_buf)

        # If video is not WebVTT, assume SRT.

        # `WebVTT.read_buffer` only supports WebVTT format, and
        # `WebVTT.from_srt` only supports file paths. We have to use the
        # underlying parser directly to import SRT from a buffer.
        parser = SRTParser().read_from_buffer(content_buf)
        return WebVTT(captions=parser.captions)


def factory(_context, request):
    return TranscriptService(http_service=request.find_service(HTTPService))
