from pyramid.httpexceptions import HTTPBadRequest, HTTPConflict


class BadURL(HTTPBadRequest):
    """An invalid URL was discovered"""


class UpstreamServiceError(HTTPConflict):
    """Something went wrong when calling an upstream service."""
