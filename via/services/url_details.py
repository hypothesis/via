"""Retrieve details about a resource at a URL."""

from collections import OrderedDict
from email.message import Message

from via.requests_tools.headers import add_request_headers, clean_headers
from via.services.checkmate import CheckmateService
from via.services.google_drive import GoogleDriveAPI
from via.services.http import HTTPService
from via.services.youtube import YouTubeService


class URLDetailsService:
    def __init__(
        self,
        checkmate_service: CheckmateService,
        http_service: HTTPService,
        youtube_service: YouTubeService,
    ):
        self._checkmate = checkmate_service
        self._http = http_service
        self._youtube = youtube_service

    def get_url_details(self, url, headers=None):
        """Get the content type and status code for a given URL.

        :param url: URL to retrieve
        :param headers: The original headers the request was made with
        :return: 2-tuple of (mime type, status code)

        :raise BadURL: if the URL is malformed
        :raise checkmatelib.BadURL: if the URL is blocked by Checkmate
        :raise UpstreamServiceError: if we get an error from the upstream server
        :raise UnhandledException: if we get any other request-based error
        """
        if self._youtube.enabled and self._youtube.get_video_id(url):
            return "video/x-youtube", 200

        self._checkmate.raise_if_blocked(url)

        if GoogleDriveAPI.parse_file_url(url):
            return "application/pdf", 200

        with self._http.get(
            url,
            stream=True,
            allow_redirects=True,
            headers=add_request_headers(clean_headers(headers or OrderedDict())),
            timeout=10,
            raise_for_status=False,
        ) as rsp:
            content_type = rsp.headers.get("Content-Type")
            if content_type:
                message = Message()
                message["content-type"] = content_type
                mime_type = message.get_content_type()
            else:
                mime_type = None

            return mime_type, rsp.status_code


def factory(_context, request):
    return URLDetailsService(
        checkmate_service=request.find_service(CheckmateService),
        http_service=request.find_service(HTTPService),
        youtube_service=request.find_service(YouTubeService),
    )
