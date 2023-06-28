import logging

from h_pyramid_sentry import report_exception as report_exception_to_sentry
from pyramid.view import (
    exception_view_config,
    forbidden_view_config,
    notfound_view_config,
    view_defaults,
)

logger = logging.getLogger(__name__)


@view_defaults(path_info="^/api/.*", renderer="json")
class APIExceptionViews:
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @exception_view_config(Exception)
    def exception(self):
        report_exception_to_sentry(self.context)
        logger.exception(self.context)

        self.request.response.status_int = 500

        return {
            "errors": [
                {
                    "status": self.request.response.status_int,
                    "code": self.context.__class__.__name__,
                    "title": str(
                        getattr(
                            self.context,
                            "cause",
                            "Something went wrong",
                        )
                    ),
                    "detail": str(self.context).strip(),
                }
            ]
        }

    @forbidden_view_config()
    def forbidden(self):
        self.request.response.status_int = 403

    @notfound_view_config()
    def notfound(self):
        self.request.response.status_int = 404
