from unittest import mock

from via import views
from via.resources import URLResource


class TestIncludeMe:
    def test_include_me(self):
        config = mock.MagicMock()

        views.includeme(config)

        assert config.add_route.call_args_list == [
            mock.call("index", "/"),
            mock.call("get_status", "/_status"),
            mock.call("view_pdf", "/pdf", factory=URLResource),
            mock.call("route_by_content", "/route", factory=URLResource),
            mock.call("debug_headers", "/debug/headers"),
            mock.call("google_drive_file", "google_drive/{file_id}"),
            mock.call("proxy", "/{url:.*}"),
        ]
        config.scan.assert_called_once_with("via.views")
