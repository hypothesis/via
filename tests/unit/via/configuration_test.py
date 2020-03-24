import pytest
from h_matchers import Any

from via.configuration import Configuration


class TestConfiguration:
    H_DEFAULTS = {"appType": "via", "showHighlights": True, "openSidebar": False}

    def test_it_ignores_items_not_marked_with_via(self):
        via_params, h_params = Configuration.extract_from_params({})
        assert via_params == {}
        assert h_params == self.H_DEFAULTS

    def test_it_leaves_unknown_root_elements_for_via(self):
        via_params, h_params = Configuration.extract_from_params(
            {"via.key_name": "value"}
        )

        assert via_params == {"key_name": "value"}
        assert h_params == self.H_DEFAULTS

    def test_it_sets_h_defaults(self):
        _, h_params = Configuration.extract_from_params({})

        assert h_params == self.H_DEFAULTS

    def test_it_extracts_nested_h_elements(self):
        _, h_params = Configuration.extract_from_params(
            {
                "via.h.request_config_from_frame.item_one": "one",
                "via.h.request_config_from_frame.item_two": "two",
            }
        )

        assert h_params == Any.dict.containing(
            {"requestConfigFromFrame": {"itemOne": "one", "itemTwo": "two"}}
        )

    def test_it_filters_non_whitelisted_h_params(self):
        _, h_params = Configuration.extract_from_params({"via.h.not_a_thing": "value"})

        assert h_params == self.H_DEFAULTS

    @pytest.mark.parametrize(
        "params,expected",
        (
            ({"via.open_sidebar": "foo"}, {"openSidebar": "foo"}),
            (
                {"via.request_config_from_frame": "foo"},
                {"requestConfigFromFrame": {"origin": "foo", "ancestorLevel": 2}},
            ),
        ),
    )
    def test_it_moves_legacy_params_to_h_config(self, params, expected):
        via_params, h_params = Configuration.extract_from_params(params)

        assert via_params == {}
        assert h_params == Any.dict.containing(expected)
