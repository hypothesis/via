"""Tools for reading in configuration."""

# pylint: disable=too-few-public-methods


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

    @staticmethod
    def _unflatten(params):
        """Convert dot delimited flat data into nested dicts.

        This method will skip any keys which do not start with "via." and will
        return a data structure rooted after that point. So "via.a.b" will
        start at "a".
        """

        data = {}

        for key, value in params.items():
            parts = key.split(".")
            if parts[0] != "via":
                continue

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
