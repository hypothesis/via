from datetime import datetime, timedelta

from jose import jwt

from via.exceptions import UpstreamServiceError
from via.requests_tools.headers import add_request_headers
from via.services import HTTPService


class JSTORAPI:
    """An interface for dealing with JSTOR documents."""

    DEFAULT_DOI_PREFIX = "10.2307"
    """Used when no DOI prefix can be found."""

    def __init__(self, api_url, secret, http_service: HTTPService):
        self._api_url = api_url
        self._http = http_service
        self._secret = secret

    @property
    def enabled(self):
        """Get whether the service is enabled for this instance."""

        return bool(self._api_url and self._secret)

    @classmethod
    def is_jstor_url(cls, url):
        """Get whether a URL is a JSTOR url."""

        return url.startswith("jstor://")

    def get_public_url(self, url, site_code):
        """Get a signed S3 URL for the given JSTOR URL.

        :param url: The URL to stream
        :param site_code: The code we use to authenticate ourselves to JSTOR
        :return: A public URL
        :raises UpstreamServiceError: If we get bad data back from the service
        """

        doi = url.replace("jstor://", "")
        if "/" not in doi:
            doi = f"{self.DEFAULT_DOI_PREFIX}/{doi}"

        token = self._get_access_token(site_code)
        s3_url = self._http.request(
            method="GET",
            url=f"{self._api_url}/pdf-url/{doi}",
            headers=add_request_headers({"Authorization": f"Bearer {token}"}),
        ).text

        if not s3_url.startswith("https://"):
            raise UpstreamServiceError(
                f"Expected to get an S3 URL but got: {s3_url} instead"
            )

        return s3_url

    def _get_access_token(self, site_code):
        return jwt.encode(
            {
                "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
                "site_code": site_code,
            },
            self._secret,
            algorithm="HS256",
        )


def factory(_context, request):
    return JSTORAPI(
        http_service=request.find_service(HTTPService),
        api_url=request.registry.settings.get("jstor_api_url", None),
        secret=request.registry.settings.get("jstor_api_secret", None),
    )
