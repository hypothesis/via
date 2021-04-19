from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config, view_defaults


@view_defaults(route_name="index")
class IndexViews:
    def __init__(self, request):
        self.request = request
        self.enabled = request.registry.settings["enable_front_page"]

    @view_config(request_method="GET", renderer="via:templates/index.html.jinja2")
    def get(self):
        if not self.enabled:
            return HTTPNotFound()

        return {}

    @view_config(request_method="POST")
    def post(self):
        if not self.enabled:
            return HTTPNotFound()

        return HTTPFound(
            self.request.route_url(
                route_name="proxy", url=self.request.params.get("url", "")
            )
        )
