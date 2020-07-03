"""Views for debugging."""

import json
from collections import OrderedDict

from pyramid import view
from pyramid.response import Response

from via.get_url import clean_headers


@view.view_config(route_name="debug_headers")
def debug_headers(_context, request):
    """Dump the headers as we receive them for debugging."""

    if request.GET.get("raw"):
        headers = OrderedDict(request.headers)
    else:
        headers = clean_headers(request.headers)

    return Response(
        body=f"""
            <h1>Instructions</h1>
            <ol>
                <li>Access the service directly (not thru *.hypothes.is)
                <li>Enable Do-Not-Track if supported</li>
                <li>
                    <a href="{request.route_url('debug_headers')}">
                        Click here to get referer
                    </a>
                </li>
                <li>Press F5 to get 'Cache-Control'</li>
            </ol>

            <a href="{request.route_url('debug_headers')}?raw=1">Show all headers</a>
            <hr>
            <pre>{json.dumps(headers, indent=4)}</pre><br>
        """,
        status=200,
    )
