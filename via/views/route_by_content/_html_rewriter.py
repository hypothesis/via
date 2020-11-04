"""Logic for interacting with HTML rewriters."""
from urllib.parse import parse_qsl, urlencode, urlparse

from webob.multidict import MultiDict


class HTMLRewriter:
    """A service for creating URLs for HTML rewriting engines."""

    @classmethod
    def from_request(cls, request):
        """Get an instance of HTMLRewriter from a pyramid Request object."""

        return cls(
            via_html_url=request.registry.settings["via_html_url"],
        )

    def __init__(self, via_html_url):
        """Create an HTMLRewriter.

        :param via_html_url: URL to use for internal rewriting module
        """
        self._via_html_url = via_html_url

    def url_for(self, params):
        """Get the rewriter URL to return based on the passed params.

        This will extract the document url from the `url` parameter and then
        format it together with the URL for the rewriter engine.

        By default this is Via 1, but if `via.rewrite` query parameter is set
        to a truthy value, the internal rewriter will be used instead.

        :param params: A mapping of query params
        :return: URL to redirect the user to to view the document and whether
            it's cacheable as a tuple
        """

        # Get the query we were called with and remove the url
        query = MultiDict(params)
        raw_url = urlparse(query.pop("url"))

        # Create a pywb compatible URL by concatenating the urls
        bare_url = raw_url._replace(query=None).geturl()
        rewriter_url = urlparse(f"{self._via_html_url}/{bare_url}")

        # Add the merged query parameters
        query.update(parse_qsl(raw_url.query))
        rewriter_url = rewriter_url._replace(query=urlencode(query))

        return rewriter_url.geturl()
