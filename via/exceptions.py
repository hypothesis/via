"""Application specific exceptions."""

from pyramid.httpexceptions import HTTPBadRequest, HTTPConflict, HTTPExpectationFailed
from requests import exceptions

# pylint: disable=too-many-ancestors
# It's ok to have a hierarchy of exceptions

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


class BadURL(HTTPBadRequest):
    """An invalid URL was discovered."""


class UpstreamServiceError(HTTPConflict):
    """Something went wrong when calling an upstream service."""


class UnhandledException(HTTPExpectationFailed):
    """Something we did not plan for went wrong."""
