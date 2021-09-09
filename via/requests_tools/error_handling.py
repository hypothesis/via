"""Helpers for capturing requests exceptions."""

from functools import wraps

from requests import RequestException, exceptions

from via.exceptions import BadURL, UnhandledUpstreamException, UpstreamServiceError

DEFAULT_ERROR_MAP = {
    exceptions.MissingSchema: BadURL,
    exceptions.InvalidSchema: BadURL,
    exceptions.InvalidURL: BadURL,
    exceptions.URLRequired: BadURL,
    exceptions.ConnectionError: UpstreamServiceError,
    exceptions.Timeout: UpstreamServiceError,
    exceptions.TooManyRedirects: UpstreamServiceError,
    exceptions.SSLError: UpstreamServiceError,
    RequestException: UnhandledUpstreamException,
}


def handle_errors(inner):
    """Translate errors into our application errors."""

    @wraps(inner)
    def deco(*args, **kwargs):
        try:
            return inner(*args, **kwargs)

        except Exception as err:
            # Pylint thinks we are raising None, but the if takes care of it
            # pylint: disable=raising-bad-type
            if mapped_err := _translate_error(err, DEFAULT_ERROR_MAP):
                raise mapped_err from err

            raise

    return deco


def iter_handle_errors(inner):
    """Translate errors into our application errors."""

    @wraps(inner)
    def deco(*args, **kwargs):
        try:
            yield from inner(*args, **kwargs)

        except Exception as err:
            # Pylint thinks we are raising None, but the if takes care of it
            # pylint: disable=raising-bad-type
            if mapped_err := _translate_error(err, DEFAULT_ERROR_MAP):
                raise mapped_err from err

            raise

    return deco


def _translate_error(err, mapping):
    for error_class, target_class in mapping.items():
        if isinstance(err, error_class):
            return target_class(err.args[0] if err.args else None)

    return None
