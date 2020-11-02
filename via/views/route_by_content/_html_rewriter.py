"""Logic for interacting with HTML rewriters."""
import os
from random import random
from urllib.parse import parse_qsl, urlencode, urlparse

from h_vialib import Configuration
from pyramid.settings import asbool
from webob.multidict import MultiDict


class HTMLRewriter:
    """A service for creating URLs for HTML rewriting engines."""

    @classmethod
    def from_request(cls, request):
        """Get an instance of HTMLRewriter from a pyramid Request object."""

        return cls(
            legacy_via_url=request.registry.settings["legacy_via_url"],
            via_html_url=request.registry.settings.get("via_html_url"),
        )

    def __init__(self, legacy_via_url, via_html_url=None):
        """Create an HTMLRewriter.

        :param legacy_via_url: URL to use for original Via
        :param via_html_url: URL to use for internal rewriting module
        """
        self.legacy_via_url = legacy_via_url
        self.via_html_url = via_html_url or legacy_via_url

    def url_for(self, params):
        """Get the rewriter URL to return based on the passed params.

        This will extract the document url from the `url` parameter and then
        format it together with the URL for the rewriter engine.

        By default this is Via 1, but if `via.rewrite` query parameter is set
        to a truthy value, the internal rewriter will be used instead.

        :param params: A mapping of query params
        :return: URL to redirect the user to to view the document
        """

        rewriter_url = self._html_rewriter_url(params)
        return self._merge_params(rewriter_url, params)

    def _html_rewriter_url(self, params):
        via_config, _ = Configuration.extract_from_params(params)

        use_via_html = asbool(via_config.get("rewrite"))
        if not use_via_html:
            # Redirect a random portion of requests to ViaHTML if requested
            try:
                via_html_ratio = float(os.environ.get("VIA_HTML_RATIO", 0))
            except ValueError:
                via_html_ratio = 0.0

            if random() < via_html_ratio:
                use_via_html = True

        if use_via_html:
            # Attempt to enable internal rewriter if `via.rewrite` is in the
            # query string and truthy

            return self.via_html_url

        return self.legacy_via_url

    @classmethod
    def _merge_params(cls, rewriter_url, params):
        # Get the query we were called with and remove the url

        query = MultiDict(params)
        raw_url = urlparse(query.pop("url"))

        # Create a pywb compatible URL by concatenating the urls
        bare_url = raw_url._replace(query=None).geturl()
        rewriter_url = urlparse(f"{rewriter_url}/{bare_url}")

        # Add the merged query parameters
        query.update(parse_qsl(raw_url.query))
        rewriter_url = rewriter_url._replace(query=urlencode(query))

        return rewriter_url.geturl()
