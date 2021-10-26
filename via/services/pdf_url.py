import hashlib
from base64 import b64encode
from dataclasses import dataclass
from datetime import timedelta
from typing import Callable

from h_vialib.secure import quantized_expiry

from via.services.google_drive import GoogleDriveAPI
from via.services.secure_link import SecureLinkService


@dataclass
class _NGINXSigner:
    nginx_server: str
    secret: str

    def sign_url(self, url, nginx_path):
        """Return the URL from which the PDF viewer should load the PDF."""

        # Compute the expiry time to put into the URL.
        exp = int(quantized_expiry(max_age=timedelta(hours=25)).timestamp())

        # The expression to be hashed.
        #
        # This matches the hash expression that we tell the NGINX secure link
        # module to use with the secure_link_md5 setting in our NGINX config file.
        #
        # http://nginx.org/en/docs/http/ngx_http_secure_link_module.html#secure_link_md5
        hash_expression = f"{nginx_path}{exp}/{url} {self.secret}"

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
        return f"{self.nginx_server}{nginx_path}{sec}/{exp}/{url}"


@dataclass
class PDFURLBuilder:
    google_drive_api: GoogleDriveAPI
    secure_link_service: SecureLinkService
    route_url: Callable
    nginx_signer: _NGINXSigner

    def get_pdf_url(self, url):
        """Build a signed URL to the corresponding Via route for proxing the PDF at `url`.

        By default PDFs will be proxied by Nginx but we'll dispatch based on the URL
        to other routes responsible of proxing PDFs from Google Drive or MS OneDrive.
        """
        if file_details := self.google_drive_api.parse_file_url(url):
            return self._google_file_url(file_details, url)

        return self.nginx_signer.sign_url(url, nginx_path="/proxy/static/")

    def _google_file_url(self, file_details, url):
        route = "proxy_google_drive_file"
        if file_details.get("resource_key"):
            route += ":resource_key"

        return self.secure_link_service.sign_url(
            self.route_url(
                route,
                # Pass the original URL along so it will show up nicely in
                # error messages. This isn't useful for users as they don't
                # see this directly, but it's handy for us.
                _query={"url": url},
                **file_details,
            )
        )


def factory(_context, request):
    return PDFURLBuilder(
        google_drive_api=request.find_service(GoogleDriveAPI),
        secure_link_service=request.find_service(SecureLinkService),
        route_url=request.route_url,
        nginx_signer=_NGINXSigner(
            nginx_server=request.registry.settings["nginx_server"],
            secret=request.registry.settings["nginx_secure_link_secret"],
        ),
    )
