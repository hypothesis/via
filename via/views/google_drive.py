from pyramid.httpexceptions import HTTPNoContent
from pyramid.view import view_config

from via.services import GoogleDriveAPI, ProxyPDFService
from via.services.secure_link import has_secure_url_token


@view_config(route_name="proxy_google_drive_file", decorator=(has_secure_url_token,))
@view_config(
    route_name="proxy_google_drive_file:resource_key", decorator=(has_secure_url_token,)
)
def proxy_google_drive_file(request):
    """Proxy a file from Google Drive."""

    # Add an iterable to stream the content instead of holding it all in memory
    content_iterable = ProxyPDFService.reify_first(
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
    response.headers.update(ProxyPDFService.response_headers())

    response.app_iter = content_iterable
    return response
