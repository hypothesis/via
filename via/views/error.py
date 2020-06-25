"""Error views to handle when things go wrong in the app."""

from pyramid.httpexceptions import (
    HTTPClientError,
    HTTPError,
    HTTPExpectationFailed,
    HTTPNotFound,
)
from pyramid.view import exception_view_config

from via.exceptions import BadURL, UnhandledException, UpstreamServiceError

ERROR_MAP = {
    BadURL: {
        "title": "Oops, that URL doesn't look right",
        "long_description": [
            "This URL doesn't look right, so we couldn't try to get the web page.",
            "Parts could be missing or in the wrong format.",
        ],
        "stage": "request",
        "retryable": False,
    },
    UpstreamServiceError: {
        "title": "We couldn't get that web page for you",
        "long_description": [
            "We had problems getting the web page.",
            "This looks like a problem with the web page itself.",
        ],
        "stage": "upstream",
        "retryable": True,
    },
    UnhandledException: {
        "title": "Something went wrong",
        "long_description": [
            "Something we didn't expect happened.",
            "Retrying might help, but if you get this error repeatedly please report it.",
        ],
        "stage": "via",
        "retryable": True,
    },
    HTTPNotFound: {
        "title": "Oops, we can't find that!",
        "long_description": [
            "The URL you have entered isn't part of this service.",
            "Please check the URL you have entered.",
        ],
        "stage": "request",
        "retryable": False,
    },
    HTTPClientError: {
        "title": "Oops, we can't do that!",
        "long_description": [
            "Something is wrong with the request made to us.",
            "We can't understand it to try and get the web page for you.",
        ],
        "stage": "request",
        "retryable": False,
    },
}


def _get_meta(error):
    """Convert an unhandled error into an managed error."""

    meta = ERROR_MAP.get(type(error))
    if meta:
        return meta

    for error_type, meta in ERROR_MAP.items():
        if isinstance(error, error_type):
            return meta

    return ERROR_MAP.get(UnhandledException)


@exception_view_config(Exception, renderer="via:templates/error.jinja2")
@exception_view_config(HTTPError, renderer="via:templates/error.jinja2")
def error_view(exc, request):
    """Catch all errors (Pyramid or Python) and display an HTML page."""

    try:
        status_code = exc.status_int
    except AttributeError:
        # This is our 501, chosen to not scare Cloudflare.
        status_code = HTTPExpectationFailed.code  # 417

    request.response.status_int = status_code

    error_meta = _get_meta(exc)
    error_meta.update({"class": exc.__class__.__name__, "details": str(exc)})

    return {
        "status_code": status_code,
        "error": error_meta,
        "url": {"original": request.GET.get("url", None), "retry": request.url},
    }
