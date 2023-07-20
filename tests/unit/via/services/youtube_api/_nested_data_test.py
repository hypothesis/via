import pytest
from pytest import param

from via.services.youtube_api import safe_get


class TestSafeGet:
    @pytest.mark.parametrize(
        "data,path,expected",
        (
            param({"a": {"b": 1}}, ["a", "b"], 1, id="nested_dict_key"),
            param({"a": 1}, ["b"], ..., id="missing_dict_key"),
            param({"a": None}, ["a"], None, id="null_not_default"),
            param({"a": None}, ["a", "b"], ..., id="dict_key_into_none"),
            param({"a": [{"b": 1}]}, ["a", 0, "b"], 1, id="array_key"),
            param({"a": [{"b": 1}]}, ["a", 1, "b"], ..., id="missing_array_key"),
        ),
    )
    def test_it(self, data, path, expected):
        assert safe_get(data, path, default=...) == expected
