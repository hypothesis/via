"""Logic for interacting with HTML rewriters."""

from urllib.parse import parse_qsl, urlencode, urlparse

from pyramid.settings import asbool
from webob.multidict import MultiDict

from via.configuration import Configuration

# pylint: disable=too-few-public-methods


def html_rewriter_factory(request):
    """Get an instance of HTMLRewriter from a pyramid Request object."""

    return HTMLRewriter(
        legacy_via_url=request.registry.settings["legacy_via_url"],
        internal_rewriter_url=request.registry.settings.get("internal_rewriter_url"),
    )


class HTMLRewriter:
    """A service for creating URLs for HTML rewriting engines."""

    def __init__(self, legacy_via_url, internal_rewriter_url=None):
        """Create an HTMLRewriter.

        :param legacy_via_url: URL to use for original Via
        :param internal_rewriter_url: URL to use for internal rewriting module
        """
        self.legacy_via_url = legacy_via_url
        self.internal_rewriter_url = internal_rewriter_url or legacy_via_url

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

        if asbool(via_config.get("rewrite")):
            # Attempt to enable internal rewriter if `via.rewrite` is in the
            # query string and truthy

            return self.internal_rewriter_url

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
