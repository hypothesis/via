import requests

from via.requests_tools import add_request_headers, stream_bytes
from via.requests_tools.error_handling import iter_handle_errors


class ProxyPDFService:
    TIMEOUT = 30

    @iter_handle_errors(None)
    def iter_url(self, url):
        response = requests.get(
            url=url,
            headers=add_request_headers(
                {
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate",
                    "User-Agent": "(gzip)",
                }
            ),
            stream=True,
            timeout=self.TIMEOUT,
        )
        response.raise_for_status()

        return stream_bytes(response)


def factory(_context, _request):
    return ProxyPDFService()
