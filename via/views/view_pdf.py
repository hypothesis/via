"""View presenting the PDF viewer."""

from itertools import chain

from h_vialib import Configuration
from pyramid.httpexceptions import HTTPNoContent
from pyramid.view import view_config

from via.services import GoogleDriveAPI, HTTPService
from via.services.pdf_url import PDFURLBuilder
from via.services.secure_link import has_secure_url_token


@view_config(
    renderer="via:templates/pdf_viewer.html.jinja2",
    route_name="view_pdf",
    # We have to keep the leash short here for caching so we can pick up new
    # immutable assets when they are deployed
    http_cache=0,
    decorator=(has_secure_url_token,),
)
def view_pdf(context, request):
    """HTML page with client and the PDF embedded."""

    url = context.url_from_query()
    request.checkmate.raise_if_blocked(url)

    _, h_config = Configuration.extract_from_params(request.params)

    return {
        # The upstream PDF URL that should be associated with any annotations.
        "pdf_url": url,
        # The CORS-proxied PDF URL which the viewer should actually load the
        # PDF from.
        "proxy_pdf_url": request.find_service(PDFURLBuilder).get_pdf_url(url),
        "client_embed_url": request.registry.settings["client_embed_url"],
        "static_url": request.static_url,
        "hypothesis_config": h_config,
    }


@view_config(route_name="proxy_one_drive_pdf", decorator=(has_secure_url_token,))
def proxy_one_drive_pdf(context, request):
    url = context.url_from_query()

    content_iterable = request.find_service(HTTPService).stream(url)

    return _iter_pdf_response(request.response, content_iterable)


@view_config(route_name="proxy_google_drive_file", decorator=(has_secure_url_token,))
@view_config(
    route_name="proxy_google_drive_file:resource_key", decorator=(has_secure_url_token,)
)
def proxy_google_drive_file(request):
    """Proxy a file from Google Drive."""

    # Add an iterable to stream the content instead of holding it all in memory
    content_iterable = request.find_service(GoogleDriveAPI).iter_file(
        file_id=request.matchdict["file_id"],
        resource_key=request.matchdict.get("resource_key"),
    )

    return _iter_pdf_response(request.response, content_iterable)


def _iter_pdf_response(response, content_iterable):

    try:
        # Get an iterable where the first item only has already been reified.
        # Return None if there is no content to return.
        # This takes a potentially lazy generator, and ensures the first item is
        # called now. This is so any errors or problems that come from starting the
        # process happen immediately, rather than whenever the iterable is evaluated.
        content_iterable = chain((next(content_iterable),), content_iterable)
    except StopIteration:
        # Respond with 204 no content for empty files. This means they won't be
        # cached by Cloudflare and gives the user a chance to fix the problem.
        return HTTPNoContent()

    response.headers.update(
        {
            "Content-Disposition": "inline",
            "Content-Type": "application/pdf",
            # Add a very generous caching policy of half a day max-age, full
            # day stale while revalidate.
            "Cache-Control": "public, max-age=43200, stale-while-revalidate=86400",
        }
    )

    response.app_iter = content_iterable
    return response
