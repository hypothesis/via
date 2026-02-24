from urllib.parse import urlparse

from pyramid.httpexceptions import HTTPBadRequest, HTTPFound, HTTPNotFound
from pyramid.view import view_config, view_defaults

from via.services import SecureLinkService


@view_defaults(route_name="index")
class IndexViews:
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.enabled = request.registry.settings["enable_front_page"]

    def _is_lms_request(self):
        """Check if request comes from LMS (has a valid signed URL)."""
        return self.request.find_service(SecureLinkService).request_has_valid_token(
            self.request
        )

    @view_config(request_method="GET", renderer="via:templates/index.html.jinja2")
    def get(self):
        # Allow LMS access, otherwise show restricted page
        if not self._is_lms_request():
            self.request.override_renderer = "via:templates/restricted.html.jinja2"
            return {"target_url": None}

        if not self.enabled:
            return HTTPNotFound()

        self.request.response.headers["X-Robots-Tag"] = "all"

        return {}

    @view_config(request_method="POST")
    def post(self):
        # Allow LMS access, otherwise show restricted page
        if not self._is_lms_request():
            self.request.override_renderer = "via:templates/restricted.html.jinja2"
            return {"target_url": None}

        if not self.enabled:
            return HTTPNotFound()

        try:
            url = self.context.url_from_query()
        except HTTPBadRequest:
            return HTTPFound(self.request.route_url(route_name="index"))

        parsed = urlparse(url)
        url_without_query = parsed._replace(query="", fragment="").geturl()

        return HTTPFound(
            self.request.route_url(
                route_name="proxy", url=url_without_query, _query=parsed.query
            )
        )
