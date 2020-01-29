"""Methods and data relating to query parameters."""

from urllib.parse import urlencode, urlparse

from webob.multidict import MultiDict


class QueryParams:
    """Client configuration query parameters and related functions."""

    # pylint: disable=too-few-public-methods

    OPEN_SIDEBAR = "via.open_sidebar"
    CONFIG_FROM_FRAME = "via.request_config_from_frame"
    ALL_PARAMS = {OPEN_SIDEBAR, CONFIG_FROM_FRAME}

    @classmethod
    def build_url(cls, url, query, strip_via_params):
        """Add the query to the url, optionally removing via related params.

        :param url: URL to base the new URL on
        :param query: Dict of query parameters
        :param strip_via_params: Enable removal of via params
        :return: A new URL with the relevant query params added
        """

        # Coerce any immutable NestedMultiDict's into mutable a MultiDict
        if strip_via_params:
            query = MultiDict(query)

            via_keys = [key for key in query.keys() if key in cls.ALL_PARAMS]
            for key in via_keys:
                query.pop(key, None)

        return urlparse(url)._replace(query=urlencode(query)).geturl()
