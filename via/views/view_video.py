from pyramid.view import view_config


@view_config(
    renderer="via:templates/restricted.html.jinja2",
    route_name="youtube",
)
def youtube(context, _request):
    """Show restricted access page instead of the YouTube viewer."""
    try:
        target_url = context.url_from_query()
    except Exception:  # noqa: BLE001
        target_url = None

    return {"target_url": target_url}


@view_config(
    route_name="video",
    renderer="via:templates/restricted.html.jinja2",
)
def video(_context, request):
    """Show restricted access page instead of the video viewer."""
    target_url = request.params.get("url")
    return {"target_url": target_url}
