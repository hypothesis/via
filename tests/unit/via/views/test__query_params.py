import pytest
from webob.multidict import MultiDict, NestedMultiDict

from via.views._query_params import QueryParams


class TestQueryParams:
    ORIGINAL_URL = "http://example.com"

    @pytest.mark.parametrize(
        "params",
        [
            {},
            {QueryParams.CONFIG_FROM_FRAME: "test_1"},
            {
                QueryParams.CONFIG_FROM_FRAME: "test_1",
                QueryParams.OPEN_SIDEBAR: "test_2",
            },
        ],
    )
    def test_build_url_strips_via_params(self, params):
        params.update({"p1": "v1", "p2": "v2"})

        url = QueryParams.build_url(self.ORIGINAL_URL, params, strip_via_params=True)

        assert url == self.ORIGINAL_URL + "?p1=v1&p2=v2"

    def test_upper_case_params_are_different(self):
        param = QueryParams.OPEN_SIDEBAR.upper()
        url = QueryParams.build_url(
            self.ORIGINAL_URL, {param: "test_1"}, strip_via_params=True
        )

        assert url == f"http://example.com?{param}=test_1"

    def test_build_url_can_leave_via_params(self):
        url = QueryParams.build_url(
            self.ORIGINAL_URL,
            {"a": "test_1", QueryParams.OPEN_SIDEBAR: "test_2"},
            strip_via_params=False,
        )

        assert url == self.ORIGINAL_URL + "?a=test_1&via.open_sidebar=test_2"

    def test_build_url_handles_multi_dicts(self):
        url = QueryParams.build_url(
            self.ORIGINAL_URL,
            NestedMultiDict(
                MultiDict({"a": "a1", QueryParams.OPEN_SIDEBAR: "v1"}),
                MultiDict({"a": "a2", QueryParams.OPEN_SIDEBAR: "v2"}),
            ),
            strip_via_params=True,
        )

        assert url == self.ORIGINAL_URL + "?a=a1&a=a2"

    @pytest.mark.parametrize("url", ["", "jddf://example.com", "http://"])
    def test_build_url_handles_malformed_urls(self, url):
        QueryParams.build_url(url, {}, strip_via_params=True)
