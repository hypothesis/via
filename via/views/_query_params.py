"""Methods and data relating to query parameters."""

from urllib.parse import urlencode

# Client configuration query parameters.
OPEN_SIDEBAR = "via.open_sidebar"
CONFIG_FROM_FRAME = "via.request_config_from_frame"


def strip_client_query_params(base_url, query_params):
    """Return ``base_url`` with non-Via params from ``query_params`` appended.

    Return ``base_url`` with all the non-Via query params from ``query_params``
    appended to it as a query string. Any params in ``query_params`` that are
    meant for Via (the ``"via.*`` query params) will be ignored and *not*
    appended to the returned URL.

    :param base_url: the protocol, domain and path, for example: https://thirdparty.url/foo.pdf
    :type base_url: str

    :param query_params: the query params to be added to base_url
    :type query_params: dict

    :return: ``base_url`` with the non-Via query params appended
    :rtype: str
    """
    client_params = [OPEN_SIDEBAR, CONFIG_FROM_FRAME]
    filtered_params = urlencode(
        {
            param: value
            for param, value in query_params.items()
            if param not in client_params
        }
    )
    if filtered_params:
        return f"{base_url}?{filtered_params}"
    return base_url
