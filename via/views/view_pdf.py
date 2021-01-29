"""View presenting the PDF viewer."""
import datetime
import hashlib
import json
from base64 import b64encode

from h_vialib import Configuration
from markupsafe import Markup
from pyramid import view


@view.view_config(
    renderer="via:templates/pdf_viewer.html.jinja2",
    route_name="view_pdf",
    # We have to keep the leash short here for caching so we can pick up new
    # immutable assets when they are deployed
    http_cache=0,
)
def view_pdf(context, request):
    """HTML page with client and the PDF embedded."""

    nginx_server = request.registry.settings["nginx_server"]
    pdf_url = _pdf_url(context.url())

    _, h_config = Configuration.extract_from_params(request.params)

    return {
        "pdf_url": _string_literal(pdf_url),
        "client_embed_url": _string_literal(
            request.registry.settings["client_embed_url"]
        ),
        "static_url": request.static_url,
        "hypothesis_config": h_config,
    }


def _pdf_url(url, secret="seekrit"):
    # Compute the expiry time to put into the URL.
    now = datetime.datetime.now()
    exp = (
        datetime.datetime(now.year, now.month, now.day, now.hour)
        + datetime.timedelta(hours=2)
    ).timestamp()
    exp = int(exp)

    # Compute the digest to put into the URL.
    hash_ = hashlib.md5()
    hash_.update(f"/proxy/static/{exp}/{url} {secret}".encode("utf-8"))
    sec = hash_.digest()
    sec = b64encode(sec)
    sec = sec.replace(b"+", b"-")
    sec = sec.replace(b"/", b"_")
    sec = sec.replace(b"=", b"")
    sec = sec.decode()

    # Construct the URL.
    return f"/proxy/static/{sec}/{exp}/{url}"


def _string_literal(string):
    """Return a JSON escaped, but otherwise un-modified string."""

    return Markup(json.dumps(str(string)))
