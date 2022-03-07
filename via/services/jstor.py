import re
from urllib.parse import urlparse
from typing import Optional

from via.requests_tools.headers import add_request_headers
from via.services import HTTPService


class JSTORAPI:

    DEFAULT_DOI_PREFIX = "10.2307"

    DOI_REGEXP = [
        re.compile(r"^https://www.jstor.org/stable/(?P<prefix>.*)/(?P<doi>.*)(/.*)?"),
        re.compile(r"^https://www.jstor.org/stable/(?P<doi>.*)(/.*)?"),
    ]

    def __init__(self, http_service: HTTPService, url, secret_ip):
        self._url = url
        self._secret_ip = secret_ip
        self._http = http_service

    def doi_from_url(self, url: str) -> Optional[str]:
        parsed = urlparse(url)
        url = parsed._replace(query="", fragment="").geturl()

        for regexp in JSTORAPI.DOI_REGEXP:
            if match := regexp.match(url):
                if not match.groupdict().get("prefix"):
                    return f"{JSTORAPI.DEFAULT_DOI_PREFIX}/{match['doi']}"

                return f"{match['prefix']}/{match['doi']}"

        return None

    def jstor_pdf_stream(self, doi: str):
        url = f"{self._url}/{doi}?ip={self._secret_ip}"

        return self._http.stream(
            url, headers=add_request_headers({"Accept": "application/pdf"})
        )


def factory(_context, request):
    return JSTORAPI(
        http_service=request.find_service(HTTPService),
        url=request.registry.settings["jstor_url"],
        secret_ip=request.registry.settings["jstor_secret_ip"],
    )
