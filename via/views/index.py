from urllib.parse import urlparse

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config, view_defaults

from via.views._helpers import url_from_user_input
from via.views.exceptions import BadURL


@view_defaults(route_name="index")
class IndexViews:
    def __init__(self, request):
        self.request = request
        self.enabled = request.registry.settings["enable_front_page"]

    @view_config(request_method="GET", renderer="via:templates/index.html.jinja2")
    def get(self):
        if not self.enabled:
            return HTTPNotFound()

        self.request.response.headers["X-Robots-Tag"] = "all"

        return {}

    @view_config(request_method="POST")
    def post(self):
        if not self.enabled:
            return HTTPNotFound()

        url = url_from_user_input(self.request.params.get("url", ""))
        try:
            parsed = urlparse(url)
        except ValueError as ex:
            raise BadURL(url) from ex
        url_without_query = parsed._replace(query="", fragment="").geturl()

        return HTTPFound(
            self.request.route_url(
                route_name="proxy", url=url_without_query, _query=parsed.query
            )
        )
