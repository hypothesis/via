from urllib.parse import urlparse

from pyramid.httpexceptions import HTTPBadRequest, HTTPFound, HTTPNotFound
from pyramid.view import view_config, view_defaults


@view_defaults(route_name="index")
class IndexViews:
    def __init__(self, context, request):
        self.context = context
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

        try:
            url = self.context.url_from_query()
        except HTTPBadRequest:
            # If we don't get a URL redirect the user to the index page
            return HTTPFound(self.request.route_url(route_name="index"))

        # In order to replicate the URL structure from original Via we need to
        # create a path like this:
        # http://via.host/http://proxied.site?query=1
        # This means we need to pop off the query string and then add it
        # separately from the URL, otherwise we'll get the query string encoded
        # inside the URL portion of the path.

        # `context.url_from_query` protects us from parsing failing
        parsed = urlparse(url)
        url_without_query = parsed._replace(query="", fragment="").geturl()

        return HTTPFound(
            self.request.route_url(
                route_name="proxy", url=url_without_query, _query=parsed.query
            )
        )
