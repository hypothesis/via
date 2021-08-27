from pyramid.view import view_config

from via.services.google_drive import GoogleDriveAPI
from via.services.secure_link import has_secure_url_token


@view_config(
    route_name="google_drive_file",
    decorator=(has_secure_url_token,),
)
def get_file_content(_context, request):
    """Download a file from Google Drive."""

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
    # Add an iterable to stream the content instead of holding it all in memory
    response.app_iter = request.find_service(GoogleDriveAPI).iter_file(
        request.matchdict["file_id"]
    )

    return response
