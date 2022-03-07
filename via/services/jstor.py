from via.requests_tools.headers import add_request_headers
from via.services import HTTPService


class JSTORAPI:
    DEFAULT_DOI_PREFIX = "10.2307"
    """Main DOI prefix. Used for real DOIs and non registered pseudo-DOIs with the same format"""

    def __init__(self, http_service: HTTPService, url):
        self._jstor_pdf_url = url
        self._http = http_service

    @property
    def enabled(self):
        return bool(self._jstor_pdf_url)

    def jstor_pdf_stream(self, jstor_url: str, jstor_ip: str):
        doi = jstor_url.replace("jstor://", "")
        if not "/" in doi:
            doi = f"{self.DEFAULT_DOI_PREFIX}/{doi}"

        url = f"{self._jstor_pdf_url}/{doi}?ip={jstor_ip}"
        return self._http.stream(
            url, headers=add_request_headers({"Accept": "application/pdf"})
        )


def factory(_context, request):
    return JSTORAPI(
        http_service=request.find_service(HTTPService),
        url=request.registry.settings.get("jstor_pdf_url", None),
    )
