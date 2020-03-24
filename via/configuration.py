"""Tools for reading in configuration."""

from inflection import camelize

# pylint: disable=too-few-public-methods


class Configuration:
    """Extracts configuration from params."""

    # Certain configuration options include URLs which we will read, write or
    # direct the user to. This would allow an attacker to craft a URL which
    # could do that to a user, so we whitelist harmless parameters instead
    # From: https://h.readthedocs.io/projects/client/en/latest/publishers/config/#config-settings
    H_CONFIG_WHITELIST = {
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
        h_params = via_params.pop("h", {})

        cls._to_camel_case(h_params)
        cls._filter_h_params(h_params)
        cls._move_legacy_params(via_params, h_params)

        # Set some defaults
        h_params["appType"] = "via"
        h_params.setdefault("showHighlights", True)

        return via_params, h_params

    @staticmethod
    def _unflatten(params):
        """Convert dot delimited flat data into nested dicts."""

        data = {}

        for key, value in params.items():
            parts = key.split(".")
            if parts[0] != "via":
                continue

            target = data
            # Skip the first 'via' part and then recurse to the one before last
            for part in parts[1:-1]:
                target = target.setdefault(part, {})

            # Finally set the last key to the value
            target[parts[-1]] = value

        return data

    @classmethod
    def _to_camel_case(cls, data):
        """Convert dict keys from snake to camelCase strings."""

        for key, value in data.items():
            if isinstance(value, dict):
                cls._to_camel_case(value)

            data[camelize(key, uppercase_first_letter=False)] = data.pop(key)

        return data

    @classmethod
    def _filter_h_params(cls, h_params):
        """Remove keys which are not in the whitelist."""

        for key in set(h_params.keys()) - cls.H_CONFIG_WHITELIST:
            h_params.pop(key)

    @staticmethod
    def _move_legacy_params(via_params, h_params):
        """Handle legacy params which we can't move for now."""

        # This is like to be around for a while
        h_params.setdefault("openSidebar", via_params.pop("open_sidebar", False))

        # This should be removed when LMS is refactored to send things the
        # new way
        request_config = via_params.pop("request_config_from_frame", None)
        if request_config is not None:
            h_params["requestConfigFromFrame"] = {
                "origin": request_config,
                "ancestorLevel": 2,
            }
