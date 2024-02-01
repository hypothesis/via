"""Integrate webargs (https://webargs.readthedocs.io/) with Via."""

from marshmallow.exceptions import ValidationError as MarshmallowValidationError
from webargs.pyramidparser import parser


@parser.error_handler
def handle_error(error: MarshmallowValidationError, *_args, **_kwargs):
    """Handle a validation error from webargs's Pyramid parser.

    webargs's Pyramid parser has a default error handling method that returns a
    JSON error response and swallows the original Marshmallow ValidationError.

    We don't want that behavior for Via so override webarg's Pyramid parser's
    default error handler with our own.

    See:

    https://webargs.readthedocs.io/en/latest/quickstart.html#error-handling

    :raises MarshmallowValidationError: whenever called

    """
    # Make the HTTP status for Marshmallow validation error responses be 400.
    error.status_int = 400

    # Re-raise the original Marshmallow validation error so that our exception
    # views have direct access to it.
    raise error
