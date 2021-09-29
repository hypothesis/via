from itertools import chain

from pyramid.httpexceptions import HTTPNoContent
from pyramid.view import view_config

from via.services.google_drive import GoogleDriveAPI
from via.services.secure_link import has_secure_url_token


@view_config(route_name="proxy_google_drive_file", decorator=(has_secure_url_token,))
@view_config(
    route_name="proxy_google_drive_file:resource_key", decorator=(has_secure_url_token,)
)
def proxy_google_drive_file(request):
    """Proxy a file from Google Drive."""

    # Add an iterable to stream the content instead of holding it all in memory
    content_iterable = _reify_first(
        request.find_service(GoogleDriveAPI).iter_file(
            file_id=request.matchdict["file_id"],
            resource_key=request.matchdict.get("resource_key"),
        ),
    )

    if content_iterable is None:
        # Respond with 204 no content for empty files. This means they won't be
        # cached by Cloudflare and gives the user a chance to fix the problem.
        return HTTPNoContent()

    response = request.response
    response.headers.update(
        {
            "Content-Disposition": "inline",
            # We'll just assume everything from Google Drive is a PDF
            "Content-Type": "application/pdf",
            # Add a very generous caching policy of half a day max-age, full
            # day stale while revalidate.
            "Cache-Control": "public, max-age=43200, stale-while-revalidate=86400",
        }
    )
    response.app_iter = content_iterable
    return response


def _reify_first(iterable):
    """Get an iterable where the first item only has already been reified.

    Return None if there is no content to return.

    This takes a potentially lazy generator, and ensures the first item is
    called now. This is so any errors or problems that come from starting the
    process happen immediately, rather than whenever the iterable is evaluated.
    """
    try:
        return chain((next(iterable),), iterable)
    except StopIteration:
        return None
