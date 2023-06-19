from pyramid.view import forbidden_view_config, notfound_view_config, view_defaults


@view_defaults(path_info="^/api/.*", renderer="json")
class APIExceptionViews:
    def __init__(self, request):
        self.request = request

    @forbidden_view_config()
    def forbidden(self):
        self.request.response.status_int = 403

    @notfound_view_config()
    def notfound(self):
        self.request.response.status_int = 404
