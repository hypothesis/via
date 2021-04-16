import pytest

from via.views.proxy import proxy


class TestProxy:
    @pytest.mark.parametrize(
        "path,url_to_proxy",
        [
            ("/https://example.com/foo", "https://example.com/foo"),
            ("/http://example.com/foo", "http://example.com/foo"),
            ("/example.com/foo", "https://example.com/foo"),
        ],
    )
    def test_it(self, pyramid_request, path, url_to_proxy):
        pyramid_request.path = path

        result = proxy(pyramid_request)

        assert result == {
            "src": pyramid_request.route_url(
                "route_by_content", _query={"url": url_to_proxy}
            )
        }
