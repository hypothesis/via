"""Error views to handle when things go wrong in the app."""

import h_pyramid_sentry
from pyramid.httpexceptions import HTTPClientError, HTTPNotFound
from pyramid.view import exception_view_config

from via.exceptions import BadURL, UnhandledUpstreamException, UpstreamServiceError

EXCEPTION_MAP = {
    BadURL: {
        "title": "The URL isn't valid",
        "long_description": [
            "Parts of the URL could be missing or in the wrong format."
        ],
        "stage": "request",
        "retryable": False,
    },
    UpstreamServiceError: {
        "title": "Could not get web page",
        "long_description": [
            "Something went wrong when we tried to get the web page.",
            "It might be missing or might have returned an error.",
        ],
        "stage": "upstream",
        "retryable": True,
    },
    UnhandledUpstreamException: {
        "title": "Something went wrong",
        "long_description": ["We experienced an unexpected error."],
        "stage": "via",
        "retryable": True,
    },
    HTTPNotFound: {
        "title": "Page not found",
        "long_description": [
            "The URL you asked for is not part of this service.",
            "Please check the URL you have entered.",
        ],
        "stage": "request",
        "retryable": False,
    },
    HTTPClientError: {
        "title": "Bad request",
        "long_description": [
            "We can't process the request because we don't understand it."
        ],
        "stage": "request",
        "retryable": False,
    },
}


def _get_meta(exception):
    """Convert an unhandled error into an managed error."""

    meta = EXCEPTION_MAP.get(type(exception))
    if meta:
        return meta

    for exception_type, meta in EXCEPTION_MAP.items():
        if isinstance(exception, exception_type):
            return meta

    return EXCEPTION_MAP.get(UnhandledUpstreamException)


@exception_view_config(
    Exception,
    route_name="proxy_google_drive_file",
    renderer="via:templates/exception.html.jinja2",
)
@exception_view_config(
    Exception,
    route_name="proxy_google_drive_file:resource_key",
    renderer="via:templates/exception.html.jinja2",
)
def google_drive_exceptions(exc, request):
    """Catch all errors for Google Drive and display an HTML page."""

    h_pyramid_sentry.report_exception(exc)

    return _get_error_body(exc, request)


@exception_view_config(Exception, renderer="via:templates/exception.html.jinja2")
def other_exceptions(exc, request):
    """Catch all errors (Pyramid or Python) and display an HTML page."""

    # We don't want to log errors from upstream services or things which are
    # the user goofing about making bad queries.
    if not isinstance(
        exc, (UpstreamServiceError, UnhandledUpstreamException, BadURL, HTTPClientError)
    ):
        h_pyramid_sentry.report_exception(exc)

    return _get_error_body(exc, request)


def _get_error_body(exc, request):
    try:
        status_code = exc.status_int
    except AttributeError:
        status_code = 500

    request.response.status_int = status_code

    exception_meta = _get_meta(exc)
    exception_meta.update({"class": exc.__class__.__name__, "details": str(exc)})

    return {
        "status_code": status_code,
        "exception": exception_meta,
        "url": {"original": request.GET.get("url", None), "retry": request.url},
        "static_url": request.static_url,
    }
