from unittest.mock import sentinel

import pytest

from via.services.ms_one_drive import MSOneDriveService, factory


class TestMSOneDriveService:
    @pytest.mark.parametrize(
        "url,expected",
        [
            pytest.param("https://somerandom-url.com", False),
            pytest.param(
                "https://mysharepointdomain-sharepoint.com",
                False,
                id="sharepoint missing download param",
            ),
            pytest.param(
                "https://myshare-pointdomain.sharepoint.com/FILE_ID&download=1",
                True,
                id="sharepoint file URL",
            ),
            pytest.param(
                "https://api.onedrive/v1.0/list/users",
                False,
                id="one drive domain, not file URL",
            ),
            pytest.param(
                "https://api.onedrive.com/v1.0/FILE_ID/root/content",
                True,
                id="one drive file URL",
            ),
        ],
    )
    def test_is_one_drive_url(self, url, expected):
        assert MSOneDriveService.is_one_drive_url(url) == expected

    def test_factory(self):
        assert isinstance(
            factory(sentinel.context, sentinel.request), MSOneDriveService
        )
