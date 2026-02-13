"""View presenting the PDF viewer."""

from pyramid.view import view_config


@view_config(
    renderer="via:templates/restricted.html.jinja2",
    route_name="view_pdf",
)
def view_pdf(context, _request):
    """Show restricted access page instead of the PDF viewer."""
    try:
        target_url = context.url_from_query()
    except Exception:  # noqa: BLE001
        target_url = None

    return {"target_url": target_url}


@view_config(
    route_name="proxy_onedrive_pdf",
    renderer="via:templates/restricted.html.jinja2",
)
@view_config(
    route_name="proxy_d2l_pdf",
    renderer="via:templates/restricted.html.jinja2",
)
@view_config(
    route_name="proxy_python_pdf",
    renderer="via:templates/restricted.html.jinja2",
)
def proxy_python_pdf(context, _request):
    """Show restricted access page instead of proxying PDF."""
    try:
        target_url = context.url_from_query()
    except Exception:  # noqa: BLE001
        target_url = None

    return {"target_url": target_url}


@view_config(
    route_name="proxy_google_drive_file",
    renderer="via:templates/restricted.html.jinja2",
)
@view_config(
    route_name="proxy_google_drive_file:resource_key",
    renderer="via:templates/restricted.html.jinja2",
)
def proxy_google_drive_file(_request):
    """Show restricted access page instead of proxying Google Drive file."""
    return {"target_url": None}
