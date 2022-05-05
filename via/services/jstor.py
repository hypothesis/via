import base64

from via.requests_tools.headers import add_request_headers
from via.services import HTTPService


class JSTORAPI:
    """An interface for dealing with JSTOR documents."""

    DEFAULT_DOI_PREFIX = "10.2307"
    """Used when no DOI prefix can be found."""

    def __init__(self, api_url, http_service: HTTPService):
        self._api_url = api_url
        self._http = http_service

    @property
    def enabled(self):
        """Get whether the service is enabled for this instance."""

        return bool(self._api_url)

    @classmethod
    def is_jstor_url(cls, url):
        """Get whether a URL is a JSTOR url."""

        return url.startswith("jstor://")

    def stream_pdf(self, url, jstor_ip):
        """Get a stream for the given JSTOR url.

        :param url: The URL to stream
        :param jstor_ip: The IP we use to authenticate ourselves with
        """

        doi = url.replace("jstor://", "")
        if "/" not in doi:
            doi = f"{self.DEFAULT_DOI_PREFIX}/{doi}"

        url = f"{self._api_url}/{doi}?ip={jstor_ip}"
        stream = self._http.stream(
            url, headers=add_request_headers({"Accept": "application/pdf"})
        )

        # Currently, JSTOR is sending us a stream of base 64 encoded data. This
        # isn't intentional and may change if they can fix it. For the time
        # being we need to decode this on the fly. This is both because it
        # gives the user a better time to first byte, but also because the
        # machinery that consumes this expects a stream, not a string.
        return decode_base64_stream(stream)


def decode_base64_stream(b64_stream):
    """Get a stream of decoded bytes from an input stream of base 64 bytes."""

    unprocessed = b""

    for chunk in b64_stream:
        # Take a chunk, but remove new lines which aren't part of the b64 data
        unprocessed += chunk.replace(b"\n", b"")

        # Every 4 bytes of Base 64 encode 3 octets exactly; any more or less
        # will potentially encode a partial octet. Therefore, we need to split
        # on exactly 4 bytes:
        # +-----------+-----------+-----------+-----------+
        # |    T      |     W     |     F     |     u     | 4 bytes of 64 input
        # |0 1 0 0 1 1|0 1|0 1 1 0|0 0 0 1|0 1|1 0 1 1 1 0|
        # |       M       |       a       |       n       | 3 output octets
        # +---------------+---------------+---------------+
        safe_len = 4 * (len(unprocessed) // 4)

        # We'll take that many off of the front of the unprocessed bytes
        to_process, unprocessed = unprocessed[:safe_len], unprocessed[safe_len:]

        # It could be we got a very small chunk, and there aren't enough bytes
        # to process
        if to_process:
            yield base64.b64decode(to_process)

    # Clear up any remaining and add extra padding to ensure we can decode
    # regardless of the length. The b64 module doesn't care if there is too
    # much padding, but it might care about too little
    if unprocessed:
        yield base64.b64decode(unprocessed + b"====")


def factory(_context, request):
    return JSTORAPI(
        http_service=request.find_service(HTTPService),
        api_url=request.registry.settings.get("jstor_pdf_url", None),
    )
