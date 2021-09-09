"""Helpers for capturing requests exceptions."""

from functools import wraps

from requests import RequestException, exceptions

from via.exceptions import BadURL, UnhandledUpstreamException, UpstreamServiceError

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


def _get_message(err):
    return err.args[0] if err.args else None


def handle_errors(inner):
    """Translate errors into our application errors."""

    @wraps(inner)
    def deco(*args, **kwargs):
        try:
            return inner(*args, **kwargs)

        except REQUESTS_BAD_URL as err:
            raise BadURL(_get_message(err)) from err

        except REQUESTS_UPSTREAM_SERVICE as err:
            raise UpstreamServiceError(_get_message(err)) from err

        except RequestException as err:
            raise UnhandledUpstreamException(_get_message(err)) from err

    return deco


def iter_handle_errors(inner):
    """Translate errors into our application errors."""

    @wraps(inner)
    def deco(*args, **kwargs):
        try:
            yield from inner(*args, **kwargs)

        except REQUESTS_BAD_URL as err:
            raise BadURL(_get_message(err)) from None

        except REQUESTS_UPSTREAM_SERVICE as err:
            raise UpstreamServiceError(_get_message(err)) from None

        except RequestException as err:
            raise UnhandledUpstreamException(_get_message(err)) from None

    return deco
