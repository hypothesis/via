import hashlib
import re
from base64 import b64encode
from dataclasses import dataclass
from datetime import timedelta
from typing import Callable

from h_vialib.secure import quantized_expiry
from requests import Request

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
        sec_str = sec.decode()

        # Construct the URL, inserting sec and exp where our NGINX config file
        # expects to find them.
        return f"{self.nginx_server}{nginx_path}{sec_str}/{exp}/{url}"


@dataclass
class PDFURLBuilder:
    request: Request
    google_drive_api: GoogleDriveAPI
    secure_link_service: SecureLinkService
    route_url: Callable
    nginx_signer: _NGINXSigner

    _MS_ONEDRIVE_URL = (
        re.compile(r"^https://.*\.sharepoint.com/.*download=1"),
        re.compile(r"^https://api.onedrive.com/v1.0/.*/root/content"),
    )

    _D2L_URL = (re.compile(r".*\/content\/topics\/\w+\/file\?stream=1$"),)

    _MOODLE_URL = (re.compile(r".*\/webservice/.*?forcedownload=1$"),)

    def get_pdf_url(self, url):
        """Build a signed URL to the corresponding Via route for proxing the PDF at `url`.

        By default PDFs will be proxied by Nginx but we'll dispatch based on the URL
        to other routes responsible of proxing PDFs from Google Drive or MS OneDrive.
        """
        if file_details := self.google_drive_api.parse_file_url(url):
            return self._google_file_url(file_details, url)

        if self._is_onedrive_url(url):
            return self._proxy_python_pdf(url, route="proxy_onedrive_pdf")

        if self._is_d2l_url(url):
            return self._proxy_python_pdf(url, route="proxy_d2l_pdf")

        if self._is_moodle_url(url):
            return self._proxy_python_pdf(url, route="proxy_python_pdf")

        return self.nginx_signer.sign_url(url, nginx_path="/proxy/static/")

    @classmethod
    def _is_onedrive_url(cls, url):
        return any(regexp.match(url) for regexp in cls._MS_ONEDRIVE_URL)

    @classmethod
    def _is_d2l_url(cls, url):
        return any(regexp.match(url) for regexp in cls._D2L_URL)

    @classmethod
    def _is_moodle_url(cls, url):
        return any(regexp.match(url) for regexp in cls._MOODLE_URL)

    def _proxy_python_pdf(self, url, route="proxy_python_pdf"):
        """Return the URL to proxy the pdf in `url` with python instead of nginx.

        Use the generic route `proxy_python_pdf` by default or the one passed as `route` if
        a different URL is needed (for different caching requirements, stats gathering...)
        """
        query_params = {"url": url}

        if headers := self.request.params.get("via.secret.headers"):
            # Pass headers of the original request back to the PDF endpoint
            query_params["via.secret.headers"] = headers

        if query := self.request.params.get("via.secret.query"):
            # Pass extra query params to the PDF endpoint
            query_params["via.secret.query"] = query

        url = self.secure_link_service.sign_url(
            self.route_url(route, _query=query_params)
        )
        return url

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
        request=request,
        google_drive_api=request.find_service(GoogleDriveAPI),
        secure_link_service=request.find_service(SecureLinkService),
        route_url=request.route_url,
        nginx_signer=_NGINXSigner(
            nginx_server=request.registry.settings["nginx_server"],
            secret=request.registry.settings["nginx_secure_link_secret"],
        ),
    )
