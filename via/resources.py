"""Context objects for views."""
from pyramid.httpexceptions import HTTPBadRequest

# pylint: disable=too-few-public-methods


class URLRoute:
    """Methods for routes which accept a 'url'."""

    def __init__(self, request):
        self._request = request

    @property
    def url(self):
        """Get the 'url' parameter.

        :raise HTTPBadRequest: If the url is missing or empty
        """
        try:
            pdf_url = self._request.params["url"]
        except KeyError as err:
            raise HTTPBadRequest("Required parameter 'url' missing") from err

        if not pdf_url:
            raise HTTPBadRequest("Required parameter 'url' is blank")

        return pdf_url
