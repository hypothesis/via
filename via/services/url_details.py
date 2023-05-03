"""Retrieve details about a resource at a URL."""
import cgi
from collections import OrderedDict

from via.requests_tools.headers import add_request_headers, clean_headers
from via.services import HTTPService
from via.services.google_drive import GoogleDriveAPI
from via.services.youtube import YoutubeService


class URLDetailsService:
    def __init__(self, http_service: HTTPService):
        self._http = http_service

    def get_url_details(self, url, headers=None):
        """Get the content type and status code for a given URL.

        :param url: URL to retrieve
        :param headers: The original headers the request was made with
        :return: 2-tuple of (mime type, status code)

        :raise BadURL: When the URL is malformed
        :raise UpstreamServiceError: If we server gives us errors
        :raise UnhandledException: For all other request based errors
        """
        if headers is None:
            headers = OrderedDict()

        if GoogleDriveAPI.parse_file_url(url):
            return "application/pdf", 200

        if YoutubeService.parse_url(url):
            return "video/x-youtube", 200

        headers = add_request_headers(clean_headers(headers))

        with self._http.get(
            url,
            stream=True,
            allow_redirects=True,
            headers=headers,
            timeout=10,
            raise_for_status=False,
        ) as rsp:
            content_type = rsp.headers.get("Content-Type")
            if content_type:
                mime_type, _ = cgi.parse_header(content_type)
            else:
                mime_type = None

            return mime_type, rsp.status_code


def factory(_context, request):
    return URLDetailsService(request.find_service(HTTPService))
