from pyramid.view import view_config


@view_config(route_name="proxy", renderer="via:templates/proxy.html.jinja2")
def proxy(request):
    url = request.path[1:]  # Strip the leading "/" from the path.

    # Let people just type in "example.com" or link to
    # via.hypothes.is/example.com and have that proxy https://example.com.
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    return {"src": request.route_url("route_by_content", _query={"url": url})}
