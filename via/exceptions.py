"""Application specific exceptions."""

from pyramid.httpexceptions import HTTPBadRequest, HTTPConflict, HTTPExpectationFailed

# pylint: disable=too-many-ancestors
# It's ok to have a hierarchy of exceptions


class BadURL(HTTPBadRequest):
    """An invalid URL was discovered."""


class UpstreamServiceError(HTTPConflict):
    """Something went wrong when calling an upstream service."""


class UnhandledException(HTTPExpectationFailed):
    """Something we did not plan for went wrong."""
