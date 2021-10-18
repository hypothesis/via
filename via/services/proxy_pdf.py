from itertools import chain

import requests

from via.requests_tools import add_request_headers, stream_bytes
from via.requests_tools.error_handling import iter_handle_errors


class ProxyPDFService:
    TIMEOUT = 30

    @iter_handle_errors(None)
    def iter_url(self, url, headers=None, timeout=TIMEOUT, **kwargs):
        response = requests.get(
            url=url,
            headers=self.request_headers(headers),
            stream=True,
            timeout=timeout,
            **kwargs,
        )
        response.raise_for_status()

        yield from self.reify_first(stream_bytes(response))

    @staticmethod
    def response_headers(headers=None):
        """Add headers to the response returned to the via users.

        Takes an optional `headers` dictionary to add any extra headers or override the defaults.

        Returns a dictionary containing the the headers.
        """

        response_headers = {
            "Content-Disposition": "inline",
            "Content-Type": "application/pdf",
            # Add a very generous caching policy of half a day max-age, full
            # day stale while revalidate.
            "Cache-Control": "public, max-age=43200, stale-while-revalidate=86400",
        }
        if headers:
            response_headers.update(headers)

        return response_headers

    @classmethod
    def request_headers(cls, headers: dict = None) -> dict:
        """Add headers to the request make to the upstream server hosting the PDF.

        Takes an optional `headers` dictionary to add any extra headers or override the defaults.

        Returns a dictionary containing the the headers.
        """
        request_headers = add_request_headers(
            {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate",
                "User-Agent": "(gzip)",
            }
        )
        if headers:
            request_headers.update(headers)
        return request_headers

    @staticmethod
    def reify_first(iterable):
        """Get an iterable where the first item only has already been reified.

        Return None if there is no content to return.
        This takes a potentially lazy generator, and ensures the first item is
        called now. This is so any errors or problems that come from starting the
        process happen immediately, rather than whenever the iterable is evaluated.
        """
        try:
            return chain((next(iterable),), iterable)
        except StopIteration:
            return None


def factory(_context, _request):
    return ProxyPDFService()
