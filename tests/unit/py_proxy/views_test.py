from unittest import mock

from py_proxy import views


class TestIndexRoute:
    def test_index_renders_index_template(self, pyramid_request):
        result = views.index(pyramid_request)

        assert result == {}


class TestStatusRoute:
    def test_status_returns_200_response(self, pyramid_request):
        result = views.status(pyramid_request)

        assert result.status == "200 OK"
        assert result.status_int == 200


class TestIncludeMe:
    config = mock.MagicMock()

    views.includeme(config)

    assert config.add_route.call_args_list == [
        mock.call("index", "/"),
        mock.call("status", "/_status"),
    ]
    config.scan.assert_called_once_with("py_proxy.views")
