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

    @pytest.mark.parametrize(
        "params,expected",
        (
            ({"via.open_sidebar": "foo"}, {"openSidebar": "foo"}),
            (
                {"via.request_config_from_frame": "foo"},
                {"requestConfigFromFrame": {"origin": "foo", "ancestorLevel": 2}},
            ),
            (
                {
                    "via.request_config_from_frame": "foo",
                    "via.config_frame_ancestor_level": "3",
                },
                {"requestConfigFromFrame": {"origin": "foo", "ancestorLevel": "3"}},
            ),
        ),
    )
    def test_it_moves_legacy_params_to_client_config(self, params, expected):
        via_params, client_params = Configuration.extract_from_params(params)

        assert via_params == {}
        assert client_params == Any.dict.containing(expected)
