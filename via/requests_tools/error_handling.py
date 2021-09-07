"""Helpers for capturing requests exceptions."""

from functools import wraps
from logging import getLogger

import h_pyramid_sentry
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


LOG = getLogger(__name__)


def _summarise_requests_exception(
    exception: exceptions.RequestException, error_message
):
    """Create a summary string from details from a `RequestsException`."""
    url = f"'{exception.request.url}'" if exception.request else "unknown URL"
    status = (
        "no response"
        if exception.response is None
        else f"{exception.response.status_code}: '{exception.response.reason}'"
    )
    return f"Requests exception - {type(exception)} Got {status} from {url} ({error_message})"


def _map_exception(exception, log_errors=False):
    """Map a child of RequestsException to our exceptions.

    :param exception: Exception to map
    :param log_errors: Also log about this error
    :return: One of our exceptions or None if we don't want to map it
    """

    def _map(exception):
        for exc_class, mapped_class in ERROR_MAP.items():
            if isinstance(exception, exc_class):
                return mapped_class

        return None

    mapped_class = _map(exception)
    if not mapped_class:
        return None

    error_message = exception.args[0] if exception.args else None

    if log_errors:
        LOG.error(_summarise_requests_exception(exception, error_message))
        h_pyramid_sentry.report_exception(exception)

    return mapped_class(error_message)


def handle_errors(inner):
    """Translate errors into our application errors."""

    @wraps(inner)
    def deco(*args, **kwargs):
        try:
            return inner(*args, **kwargs)

        except Exception as err:
            if mapped := _map_exception(err):
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
            if mapped := _map_exception(err, log_errors=True):
                raise mapped from err

            raise

    return deco
