from pyramid.httpexceptions import HTTPGone
from pyramid.view import view_config


@view_config(route_name="static_fallback")
def static_fallback(_context, _request):
    """Make sure we don't try to proxy out of date static content."""

    raise HTTPGone("It appears you have requested out of date content")  # noqa: EM101, TRY003


@view_config(
    route_name="proxy",
    renderer="via:templates/restricted.html.jinja2",
)
def proxy(context, _request):
    try:
        target_url = context.url_from_path()
    except Exception:  # noqa: BLE001
        target_url = None

    return {"target_url": target_url}
