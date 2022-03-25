import requests
from requests import RequestException, exceptions

from via.exceptions import (
    BadURL,
    UnhandledUpstreamException,
    UpstreamServiceError,
    UpstreamTimeout,
)

DEFAULT_ERROR_MAP = {
    exceptions.MissingSchema: BadURL,
    exceptions.InvalidSchema: BadURL,
    exceptions.InvalidURL: BadURL,
    exceptions.URLRequired: BadURL,
    exceptions.Timeout: UpstreamTimeout,
    exceptions.ConnectionError: UpstreamServiceError,
    exceptions.TooManyRedirects: UpstreamServiceError,
    exceptions.SSLError: UpstreamServiceError,
    RequestException: UnhandledUpstreamException,
}


class HTTPService:
    """Send HTTP requests with `requests` and receive the responses."""

    def __init__(self, session=None, error_translator=None):
        # A requests session is used so that cookies are persisted across
        # requests and urllib3 connection pooling is used (which means that
        # underlying TCP connections are re-used when making multiple requests
        # to the same host, e.g. pagination).
        #
        # See https://docs.python-requests.org/en/latest/user/advanced/#session-objects
        self._session = session or requests.Session()
        self._error_translator = error_translator

    def get(self, *args, **kwargs):
        return self.request("GET", *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.request("PUT", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request("POST", *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self.request("PATCH", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request("DELETE", *args, **kwargs)

    def request(self, method, url, timeout=(10, 10), raise_for_status=True, **kwargs):
        r"""Send a request with `requests` and return the requests.Response object.

        :param method: The HTTP method to use, one of "GET", "PUT", "POST",
            "PATCH", "DELETE", "OPTIONS" or "HEAD"
        :param url: The URL to request
        :param timeout: How long (in seconds) to wait before raising an error.
            This can be a (connect_timeout, read_timeout) 2-tuple or it can be
            a single float that will be used as both the connect and read
            timeout.
            Good practice is to set this to slightly larger than a multiple of
            3, which is the default TCP packet retransmission window. See:
            https://docs.python-requests.org/en/master/user/advanced/#timeouts
            Note that the read_timeout is *not* a time limit on the entire
            response download. It's a time limit on how long to wait *between
            bytes from the server*. The entire download can take much longer.
        :param raise_for_status: Optionally raise for 4xx & 5xx response statuses.
        :param \**kwargs: Any other keyword arguments will be passed directly to
            requests.Session().request():
            https://docs.python-requests.org/en/latest/api/#requests.Session.request
        :raise request.exceptions are mapped to via's exception on DEFAULT_ERROR_MAP
        :raise UnhandledUpstreamException: For any non mapped exception raised by requests
        :raise Exception: For any non requests exception raised
        :returns: a request.Response
        """
        response = None

        try:  # pylint:disable=too-many-try-statements
            response = self._session.request(
                method,
                url,
                timeout=timeout,
                **kwargs,
            )
            if raise_for_status:
                response.raise_for_status()

        except Exception as err:
            if mapped_err := self._translate_exception(err):
                raise mapped_err from err  # pylint: disable=raising-bad-type

            raise

        return response

    def stream(self, url, method="GET", **kwargs):
        response = self.request(method=method, url=url, stream=True, **kwargs)
        try:
            yield from self._stream_bytes(response)
        except Exception as err:
            if mapped_err := self._translate_exception(err):
                raise mapped_err from err  # pylint: disable=raising-bad-type

            raise

    def _translate_exception(self, err):
        if self._error_translator and (mapped := self._error_translator(err)):
            return mapped

        for (error_class, target_class) in DEFAULT_ERROR_MAP.items():
            if isinstance(err, error_class):
                return target_class(
                    message=err.args[0] if err.args else None,
                    requests_err=err if hasattr(err, "request") else None,
                )

        return None

    @staticmethod
    def _stream_bytes(response, min_chunk_size=64000):
        """Stream content from a `requests.Response` object.

        The response must have been called with `stream=True` for this to be
        effective. This will attempt to smooth over some of the variation of block
        size to give a smoother output for upstream services calling us.
        """
        buffer = b""

        # The chunk_size appears to be a guide value at best. We often get more
        # or just about 9 bytes, so we'll do some smoothing for our callers so we
        # don't incur overhead with very short iterations of content
        for chunk in response.iter_content(chunk_size=min_chunk_size):
            buffer += chunk
            if len(buffer) >= min_chunk_size:
                yield buffer
                buffer = b""

        if buffer:
            yield buffer


def factory(_context, _request):
    return HTTPService()
