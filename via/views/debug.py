"""Views for debugging."""

import json
from collections import OrderedDict

from pyramid import view
from pyramid.response import Response


@view.view_config(route_name="debug_headers")
def debug_headers(_context, request):
    """Dump the headers as we receive them for debugging."""
    headers = OrderedDict()

    for header_name, value in request.headers.items():
        # Get around something in the stack giving us the wrong value here
        if header_name == "Dnt":
            header_name = "DNT"
        headers[header_name] = value

    # These aren't interesting to us
    headers.pop("Cookie", None)
    headers.pop("Host", None)

    # We don't care where they really came from just where Referer appears
    if "Referer" in headers:
        headers["Referer"] = "https://www.google.com/"

    return Response(
        body=f"""
            <h1>Instructions</h1>
            <ol>
                <li>Enable Do-Not-Track if supported</li>
                <li>
                    <a href="{request.route_url('debug_headers')}">
                        Click here to get referer
                    </a>
                </li>
                <li>Press F5 to get 'Cache-Control'</li>
            </ol>
            <hr>
            <pre>{json.dumps(headers, indent=4)}</pre><br>
        """,
        status=200,
    )
