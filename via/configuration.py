"""Tools for reading in configuration."""

from urllib.parse import parse_qs, parse_qsl, urlencode, urlparse


class Configuration:
    """Extracts configuration from params.

    This class will extract and separate Client and Via configuration from a
    mapping by interpreting the keys as dot delimited values.

     * After splitting on '.' the parts are interpreted as nested dict keys
     * Any keys starting with `via.*` will be processed
     * Any keys starting with `via.client.*` will be separated out
     * Keys for the client which don't match a whitelist are discarded

    For example:

    {
        "other": "ignored",
        "via.option": "value",
        "via.client.nestOne.nestTwo": "value2"
    }

    Results in:

     * Via: {"option": "value"}
     * Client : {"nestOne": {"nextTwo": "value2"}}

    No attempt is made to interpret the values for the client. The client will
    get what we were given. If this was called from query parameters, that will
    mean a string.
    """

    # Certain configuration options include URLs which we will read, write or
    # direct the user to. This would allow an attacker to craft a URL which
    # could do that to a user, so we whitelist harmless parameters instead
    # From: https://h.readthedocs.io/projects/client/en/latest/publishers/config/#config-settings
    CLIENT_CONFIG_WHITELIST = {
        # Things we use now
        "openSidebar",
        "requestConfigFromFrame",
        # Things which seem safe
        "enableExperimentalNewNoteButton",
        "externalContainerSelector",
        "focus",
        "showHighlights",
        "theme",
    }

    KEY_PREFIX = "via"

    @classmethod
    def extract_from_params(cls, params):
        """Extract Via and H config from query parameters.

        :param params: A mapping of query parameters
        :return: A tuple of Via, and H config
        """

        via_params = cls._unflatten(params)
        client_params = via_params.pop("client", {})

        cls._filter_client_params(client_params)
        cls._move_legacy_params(via_params, client_params)

        # Set some defaults
        client_params["appType"] = "via"
        client_params.setdefault("showHighlights", True)

        return via_params, client_params

    @classmethod
    def extract_from_wsgi_environment(cls, http_env):  # pragma: no cover
        """Extract Via and H config from a WSGI environment object.

        :param http_env: WSGI provided environment variable
        :return: A tuple of Via, and H config
        """
        params = parse_qs(http_env.get("QUERY_STRING"))

        return cls.extract_from_params(params)

    @classmethod
    def extract_from_url(cls, url):  # pragma: no cover
        """Extract Via and H config from a URL.

        :param url: A URL to extract config from
        :return: A tuple of Via, and H config
        """
        params = parse_qs(urlparse(url).query)

        return cls.extract_from_params(params)

    @classmethod
    def strip_from_url(cls, url):  # pragma: no cover
        """Remove any Via configuration parameters from the URL.

        If the URL has no parameters left, remove the query string entirely.
        :param url: URL to strip
        :return: A string URL with the via parts removed
        """

        # Quick exit if this cannot contain any of our params
        if cls.KEY_PREFIX not in url:
            return url

        url_parts = urlparse(url)
        _, non_via = cls.split_params(parse_qsl(url_parts.query))
        return url_parts._replace(query=urlencode(non_via)).geturl()

    @classmethod
    def add_to_url(cls, url, via_params, client_params):  # pragma: no cover
        """Add configuration parameters to a given URL.

        This will merge and preserve any parameters already on the URL.

        :param url: URL to extract from
        :param via_params: Configuration to add for Via
        :param client_params: Configuration to add for the client
        :return: The URL with expected parameters added
        """
        url_parts = urlparse(url)
        query_items = parse_qsl(url_parts.query)

        flat_params = cls._flatten(dict(via_params, client=client_params))
        query_items.extend(flat_params.items())

        return url_parts._replace(query=urlencode(query_items)).geturl()

    @classmethod
    def split_params(cls, items):
        """Split params into via and non-via params.

        :param items: An iterable of key value pairs
        :return: A tuple of (via, non-via) key-value lists
        """

        via_params = []
        non_via_params = []

        for key, value in items:
            if key.split(".")[0] == cls.KEY_PREFIX:
                via_params.append((key, value))
            else:
                non_via_params.append((key, value))

        return via_params, non_via_params

    @classmethod
    def _flatten(cls, config, so_far=None, key_prefix=KEY_PREFIX):  # pragma: no cover
        key_prefix += "."

        if so_far is None:
            so_far = {}

        for key, value in config.items():
            flat_key = key_prefix + key
            if isinstance(value, dict):
                cls._flatten(value, so_far=so_far, key_prefix=flat_key)
            else:
                so_far[flat_key] = value

        return so_far

    @classmethod
    def _unflatten(cls, params):
        """Convert dot delimited flat data into nested dicts.

        This method will skip any keys which do not start with "via." and will
        return a data structure rooted after that point. So "via.a.b" will
        start at "a".
        """

        data = {}

        via_params, _ = cls.split_params(params.items())

        for key, value in via_params:
            parts = key.split(".")
            target = data

            # Skip the first ('via') and last parts
            for part in parts[1:-1]:
                target = target.setdefault(part, {})

            # Check to see if we have a list of values (take the first)
            if isinstance(value, list):
                value = value[0] if value else ""

            # Finally set the last key to the value
            target[parts[-1]] = value

        return data

    @classmethod
    def _filter_client_params(cls, client_params):
        """Remove keys which are not in the whitelist."""

        for key in set(client_params.keys()) - cls.CLIENT_CONFIG_WHITELIST:
            client_params.pop(key)

    @staticmethod
    def _move_legacy_params(via_params, client_params):
        """Handle legacy params which we can't move for now."""

        # This is like to be around for a while
        client_params.setdefault("openSidebar", via_params.pop("open_sidebar", False))
