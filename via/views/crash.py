from pyramid.view import view_config


@view_config(route_name="crash", request_method="GET")
def crash(_request):
    raise RuntimeError("Crash")
