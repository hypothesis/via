"""Helpers for capturing requests exceptions."""

from functools import wraps

from requests import RequestException, exceptions

from via.exceptions import BadURL, UnhandledException, UpstreamServiceError

REQUESTS_BAD_URL = (
    exceptions.MissingSchema,
    exceptions.InvalidSchema,
    exceptions.InvalidURL,
    exceptions.URLRequired,
)
REQUESTS_UPSTREAM_SERVICE = (
    exceptions.ConnectionError,
    exceptions.Timeout,
    exceptions.TooManyRedirects,
    exceptions.SSLError,
)


def handle_errors(inner):
    """Translate errors into our application errors."""

    @wraps(inner)
    def deco(*args, **kwargs):
        try:
            return inner(*args, **kwargs)

        except REQUESTS_BAD_URL as err:
            raise BadURL() from err

        except REQUESTS_UPSTREAM_SERVICE as err:
            raise UpstreamServiceError() from err

        except RequestException as err:
            raise UnhandledException() from err

    return deco
