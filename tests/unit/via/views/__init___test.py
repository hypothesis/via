from unittest import mock

from via import views
from via.resources import URLRoute


class TestIncludeMe:
    def test_include_me(self):
        config = mock.MagicMock()

        views.includeme(config)

        assert config.add_route.call_args_list == [
            mock.call("get_status", "/_status"),
            mock.call("view_pdf", "/pdf", factory=URLRoute),
            mock.call("route_by_content", "/route", factory=URLRoute),
        ]
        config.scan.assert_called_once_with("via.views")
