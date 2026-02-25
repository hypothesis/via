"""View presenting the PDF viewer."""

from itertools import chain

from h_vialib import Configuration
from h_vialib.secure import Encryption
from pyramid.httpexceptions import HTTPNoContent
from pyramid.view import view_config

from via.requests_tools.headers import add_request_headers
from via.services import (
    CheckmateService,
    GoogleDriveAPI,
    HTTPService,
    SecureLinkService,
)
from via.services.pdf_url import PDFURLBuilder


def _is_lms_request(request):
    """Check if request comes from LMS (has a valid signed URL)."""
    return request.find_service(SecureLinkService).request_has_valid_token(request)


def _restricted_response(request, context=None):
    """Return the restricted access page response."""
    try:
        target_url = context.url_from_query() if context else None
    except Exception:  # noqa: BLE001
        target_url = None
    request.override_renderer = "via:templates/restricted.html.jinja2"
    return {"target_url": target_url}


@view_config(
    renderer="via:templates/pdf_viewer.html.jinja2",
    route_name="view_pdf",
    http_cache=0,
)
def view_pdf(context, request):
    """HTML page with client and the PDF embedded.

    If the request comes through LMS (valid signed URL), serve the PDF viewer.
    Otherwise, show the restricted access page.
    """
    if not _is_lms_request(request):
        return _restricted_response(request, context)

    url = context.url_from_query()
    checkmate_service = request.find_service(CheckmateService)

    checkmate_service.raise_if_blocked(url)

    _, h_config = Configuration.extract_from_params(request.params)

    return {
        "pdf_url": url,
        "proxy_pdf_url": request.find_service(PDFURLBuilder).get_pdf_url(url),
        "client_embed_url": request.registry.settings["client_embed_url"],
        "static_url": request.static_url,
        "hypothesis_config": h_config,
    }


@view_config(route_name="proxy_onedrive_pdf")
@view_config(route_name="proxy_d2l_pdf")
@view_config(route_name="proxy_python_pdf")
def proxy_python_pdf(context, request):
    """Proxy a pdf with python (as opposed to nginx).

    If the request comes through LMS (valid signed URL), proxy the PDF.
    Otherwise, show the restricted access page.
    """
    if not _is_lms_request(request):
        return _restricted_response(request, context)

    url = context.url_from_query()
    params = {}
    if "via.secret.query" in request.params:
        secure_secrets = Encryption(
            request.registry.settings["via_secret"].encode("utf-8")
        )
        params = secure_secrets.decrypt_dict(request.params["via.secret.query"])

    content_iterable = request.find_service(HTTPService).stream(
        url, headers=add_request_headers({}, request=request), params=params
    )

    return _iter_pdf_response(request.response, content_iterable)


@view_config(route_name="proxy_google_drive_file")
@view_config(route_name="proxy_google_drive_file:resource_key")
def proxy_google_drive_file(request):
    """Proxy a file from Google Drive.

    If the request comes through LMS (valid signed URL), proxy the file.
    Otherwise, show the restricted access page.
    """
    if not _is_lms_request(request):
        request.override_renderer = "via:templates/restricted.html.jinja2"
        return {"target_url": None}

    content_iterable = request.find_service(GoogleDriveAPI).iter_file(
        file_id=request.matchdict["file_id"],
        resource_key=request.matchdict.get("resource_key"),
    )

    return _iter_pdf_response(request.response, content_iterable)


def _iter_pdf_response(response, content_iterable):
    try:
        content_iterable = chain((next(content_iterable),), content_iterable)
    except StopIteration:
        return HTTPNoContent()

    response.headers.update(
        {
            "Content-Disposition": "inline",
            "Content-Type": "application/pdf",
            "Cache-Control": "public, max-age=43200, stale-while-revalidate=86400",
        }
    )

    response.app_iter = content_iterable
    return response
