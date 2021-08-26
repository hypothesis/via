"""View presenting the PDF viewer."""
import hashlib
import logging
import re
from base64 import b64encode
from datetime import timedelta

import requests
from h_vialib import Configuration
from h_vialib.secure import quantized_expiry
from pyramid import view
from pyramid.response import Response

from via.views.decorators import has_secure_url_token


@view.view_config(
    renderer="via:templates/pdf_viewer.html.jinja2",
    route_name="view_pdf",
    # We have to keep the leash short here for caching so we can pick up new
    # immutable assets when they are deployed
    http_cache=0,
    decorator=(has_secure_url_token,),
)
def view_pdf(context, request):
    """HTML page with client and the PDF embedded."""

    url = context.url()

    request.checkmate.raise_if_blocked(url)

    nginx_server = request.registry.settings["nginx_server"]
    proxy_pdf_url = _pdf_url(
        request,
        url,
        nginx_server,
        request.registry.settings["nginx_secure_link_secret"],
    )

    _, h_config = Configuration.extract_from_params(request.params)

    return {
        # The upstream PDF URL that should be associated with any annotations.
        "pdf_url": url,
        # The CORS-proxied PDF URL which the viewer should actually load the PDF from.
        "proxy_pdf_url": proxy_pdf_url,
        "client_embed_url": request.registry.settings["client_embed_url"],
        "static_url": request.static_url,
        "hypothesis_config": h_config,
    }


@view.view_config(route_name="proxy_google_drive")
def proxy_google_drive(context, request):
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    SERVICE_ACCOUNT_FILE = "/home/marcos/hypo/token.json"
    SCOPES = [
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive.metadata",
    ]
    url = request.params["url"]
    file_id = re.match(
        r"https://drive.google.com/uc\?id=(.*)&export=download", url
    ).group(1)

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("drive", "v3", credentials=credentials)
    try:
        pdf_contents = service.files().get_media(fileId=file_id).execute()
        return Response(body=pdf_contents)
    except:
        google_api_key = request.registry.settings["google_api_key"]
        response = requests.get(
            f"https://www.googleapis.com/drive/v3/files/$2?key={google_api_key}&alt=media"
        )
        response.raise_for_status()
        return Response(body=response.contents)


def _pdf_url(request, url, nginx_server, secret):
    """Return the URL from which the PDF viewer should load the PDF."""

    if url.startswith("https://drive.google.com/uc"):
        return request.route_url("proxy_google_drive", _query={"url": url})

    # Compute the expiry time to put into the URL.
    exp = int(quantized_expiry(max_age=timedelta(hours=2)).timestamp())

    # The expression to be hashed.
    #
    # This matches the hash expression that we tell the NGINX secure link
    # module to use with the secure_link_md5 setting in our NGINX config file.
    #
    # http://nginx.org/en/docs/http/ngx_http_secure_link_module.html#secure_link_md5
    hash_expression = f"/proxy/static/{exp}/{url} {secret}"

    # Compute the hash value to put into the URL.
    #
    # This implements the NGINX secure link module's hashing algorithm:
    #
    # http://nginx.org/en/docs/http/ngx_http_secure_link_module.html#secure_link_md5
    hash_ = hashlib.md5()
    hash_.update(hash_expression.encode("utf-8"))
    sec = hash_.digest()
    sec = b64encode(sec)
    sec = sec.replace(b"+", b"-")
    sec = sec.replace(b"/", b"_")
    sec = sec.replace(b"=", b"")
    sec = sec.decode()

    # Construct the URL, inserting sec and exp where our NGINX config file
    # expects to find them.
    return f"{nginx_server}/proxy/static/{sec}/{exp}/{url}"
