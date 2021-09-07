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


def handle_errors(inner):
    """Translate errors into our application errors."""

    @wraps(inner)
    def deco(*args, **kwargs):
        try:
            return inner(*args, **kwargs)

        except Exception as err:
            if mapped := _map_error(err):
                raise mapped from err

            raise

    return deco


def iter_handle_errors(error_map):
    """Translate errors into our application errors."""

    def deco(inner):
        @wraps(inner)
        def wrapper(*args, **kwargs):
            try:
                yield from inner(*args, **kwargs)

            except Exception as err:
                if mapped := _map_error(err, log_errors=True, extra_mapping=error_map):
                    raise mapped from err

                raise

        return wrapper

    return deco


def _map_error(error, log_errors=False, extra_mapping=None):
    """Map a child of RequestsException to our exceptions.

    :param error: Error to map
    :param log_errors: Also log about this error
    :return: One of our exceptions or None if we don't want to map it
    """

    error_message = error.args[0] if error.args else None

    if log_errors:
        if isinstance(error, exceptions.RequestException):
            LOG.error(_format_requests_error(error, error_message))
        else:
            LOG.error("Non-Requests exception - %s (%s)", type(error), error_message)

        h_pyramid_sentry.report_exception(error)

    mapped_class = None
    if extra_mapping:
        mapped_class = _map_by_type(error, extra_mapping)

    if not mapped_class:
        mapped_class = _map_by_type(error, ERROR_MAP)

    if not mapped_class:
        return None

    return mapped_class(error_message)


def _format_requests_error(error: exceptions.RequestException, error_message):
    """Create a summary string from details from a `RequestsException`."""

    url = f"'{error.request.url}'" if error.request else "unknown URL"
    status = (
        "no response"
        if error.response is None
        else f"{error.response.status_code}: '{error.response.reason}'"
    )
    return (
        f"Requests exception - {type(error)} Got {status} from {url} ({error_message})"
    )


def _map_by_type(error, mapping):
    for err_class, mapped_class in mapping.items():
        if isinstance(error, err_class):
            return mapped_class

    return None
