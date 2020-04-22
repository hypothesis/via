import pytest
from h_matchers import Any

from via.configuration import Configuration


class TestConfiguration:
    CLIENT_DEFAULTS = {"appType": "via", "showHighlights": True, "openSidebar": False}

    def test_it_ignores_items_not_marked_with_via(self):
        via_params, client_params = Configuration.extract_from_params({})
        assert via_params == {}
        assert client_params == self.CLIENT_DEFAULTS

    def test_it_leaves_unknown_root_elements_for_via(self):
        via_params, client_params = Configuration.extract_from_params(
            {"via.key_name": "value"}
        )

        assert via_params == {"key_name": "value"}
        assert client_params == self.CLIENT_DEFAULTS

    def test_it_sets_client_defaults(self):
        _, client_params = Configuration.extract_from_params({})

        assert client_params == self.CLIENT_DEFAULTS

    def test_it_extracts_nested_client_elements(self):
        _, client_params = Configuration.extract_from_params(
            {
                "via.client.requestConfigFromFrame.itemOne": "one",
                "via.client.requestConfigFromFrame.itemTwo": "two",
            }
        )

        assert client_params == Any.dict.containing(
            {"requestConfigFromFrame": {"itemOne": "one", "itemTwo": "two"}}
        )

    def test_it_filters_non_whitelisted_client_params(self):
        _, client_params = Configuration.extract_from_params(
            {"via.client.notAThing": "value"}
        )

        assert client_params == self.CLIENT_DEFAULTS

    def test_it_moves_legacy_open_sidebar_to_client_config(self):
        via_params, client_params = Configuration.extract_from_params(
            {"via.open_sidebar": "foo"}
        )

        assert via_params == {}
        assert client_params == Any.dict.containing({"openSidebar": "foo"})
