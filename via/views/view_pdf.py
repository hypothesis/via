"""View presenting the PDF viewer."""
import hashlib
from base64 import b64encode
from datetime import timedelta

from h_vialib import Configuration
from h_vialib.secure import quantized_expiry
from pyramid import view

from via.services import GoogleDriveAPI
from via.services.secure_link import SecureLinkService, has_secure_url_token


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

    google_drive_api = request.find_service(GoogleDriveAPI)
    if google_drive_api.is_available and (
        file_id := google_drive_api.google_drive_id(url)
    ):
        proxy_pdf_url = request.find_service(SecureLinkService).sign_url(
            request.route_url("google_drive_file", file_id=file_id)
        )

    else:
        proxy_pdf_url = _pdf_url(
            url,
            nginx_server=request.registry.settings["nginx_server"],
            secret=request.registry.settings["nginx_secure_link_secret"],
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


def _pdf_url(url, nginx_server, secret):
    """Return the URL from which the PDF viewer should load the PDF."""

    # Compute the expiry time to put into the URL.
    exp = int(quantized_expiry(max_age=timedelta(hours=25)).timestamp())

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
