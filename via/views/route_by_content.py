"""View for redirecting based on content type."""

from pyramid import view


@view.view_config(
    route_name="route_by_content",
    renderer="via:templates/restricted.html.jinja2",
)
def route_by_content(context, _request):
    """Show restricted access page instead of routing content."""
    try:
        target_url = context.url_from_query()
    except Exception:  # noqa: BLE001
        target_url = None

    return {"target_url": target_url}
