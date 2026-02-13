from pyramid.view import view_config


@view_config(
    route_name="index",
    renderer="via:templates/restricted.html.jinja2",
)
def index(_context, _request):
    """Show restricted access page."""
    return {"target_url": None}
