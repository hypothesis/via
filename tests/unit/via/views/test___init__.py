from unittest import mock

from via import views


class TestIncludeMe:
    config = mock.MagicMock()

    views.includeme(config)

    assert config.add_route.call_args_list == [
        mock.call("get_status", "/_status"),
        mock.call("view_pdf", "/pdf/{pdf_url:.*}"),
        mock.call("route_by_content", "/{url:.*}"),
    ]
    config.scan.assert_called_once_with("via.views")
