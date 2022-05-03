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

    def stream_pdf(self, url, jstor_ip):
        """Get a stream for the given JSTOR url.

        :param url: The URL to stream
        :param jstor_ip: The IP we use to authenticate ourselves with
        """

        doi = url.replace("jstor://", "")
        if "/" not in doi:
            doi = f"{self.DEFAULT_DOI_PREFIX}/{doi}"

        url = f"{self._api_url}/{doi}?ip={jstor_ip}"
        return self._http.stream(
            url, headers=add_request_headers({"Accept": "application/pdf"})
        )


def factory(_context, request):
    return JSTORAPI(
        http_service=request.find_service(HTTPService),
        api_url=request.registry.settings.get("jstor_pdf_url", None),
    )
