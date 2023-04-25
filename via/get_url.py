"""Retrieve details about a resource at a URL."""
import cgi
from collections import OrderedDict

from via.requests_tools.headers import add_request_headers, clean_headers
from via.services.google_drive import GoogleDriveAPI
from via.services.youtube import YoutubeAPI


def get_url_details(http_service, url, headers=None):
    """Get the content type and status code for a given URL.

    :param http_service: Instance of HTTPService to make the request with
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

    if YoutubeAPI.parse_file_url(url):
        # TODO is inventing a mimetype the right approach?
        return "video/youtube", 200

    headers = add_request_headers(clean_headers(headers))

    with http_service.get(
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
