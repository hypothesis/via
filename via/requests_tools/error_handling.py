"""Helpers for capturing requests exceptions."""

from functools import wraps

from requests import exceptions

from via.exceptions import BadURL, UnhandledException, UpstreamServiceError

ERROR_MAP = {
    # The user gave us a goofy URL
    exceptions.MissingSchema: BadURL,
    exceptions.InvalidSchema: BadURL,
    exceptions.InvalidURL: BadURL,
    exceptions.URLRequired: BadURL,
    # We got something unexpected from the upstream server
    exceptions.ConnectionError: UpstreamServiceError,
    exceptions.Timeout: UpstreamServiceError,
    exceptions.TooManyRedirects: UpstreamServiceError,
    exceptions.SSLError: UpstreamServiceError,
    # Anything else...
    exceptions.RequestException: UnhandledException,
}


def map_exception(exception):
    def _map_exception(exception):
        for exc_class, mapped_class in ERROR_MAP.items():
            if isinstance(exception, exc_class):
                return mapped_class

        return None

    mapped_class = _map_exception(exception)
    if not mapped_class:
        return None

    return mapped_class(exception.args[0] if exception.args else None)


def handle_errors(inner):
    """Translate errors into our application errors."""

    @wraps(inner)
    def deco(*args, **kwargs):
        try:
            return inner(*args, **kwargs)

        except Exception as err:
            if mapped := map_exception(err):
                raise mapped from err

            raise

    return deco


def iter_handle_errors(inner):
    """Translate errors into our application errors."""

    @wraps(inner)
    def deco(*args, **kwargs):
        try:
            yield from inner(*args, **kwargs)

        except Exception as err:
            if mapped := map_exception(err):
                raise mapped from err

            raise

    return deco
