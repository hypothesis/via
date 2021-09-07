from unittest.mock import sentinel

import pytest
from h_matchers import Any
from requests import TooManyRedirects

from via.exceptions import ConfigurationError, UpstreamServiceError
from via.services.google_drive import GoogleDriveAPI


class TestGoogleDriveAPI:
    def test_it_builds_a_session_as_we_expect(
        self, api, Credentials, AuthorizedSession
    ):
        Credentials.from_service_account_info.assert_called_once_with(
            sentinel.credentials, scopes=GoogleDriveAPI.SCOPES
        )
        AuthorizedSession.assert_called_once_with(
            Credentials.from_service_account_info.return_value,
        )
        # pylint: disable=protected-access
        assert api._session == AuthorizedSession.return_value

    def test_it_with_bad_credentials(self, Credentials):
        # Google seems to raise plain ValueError's for bad config
        Credentials.from_service_account_info.side_effect = ValueError

        with pytest.raises(ConfigurationError):
            GoogleDriveAPI([sentinel.bad_credentials])

    def test_iter_file(self, api, stream_bytes):
        # This is all a bit black box, we don't necessarily know what all these
        # Google objects do, so we'll just check we call them in the right way
        stream_bytes.return_value = range(3)

        result = list(api.iter_file("FILE_ID"))

        # pylint: disable=no-member,protected-access
        api._session.get.assert_called_once_with(
            url="https://www.googleapis.com/drive/v3/files/FILE_ID?alt=media",
            headers={
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate",
                "User-Agent": "(gzip)",
                # This is looked up from the resource mapping
                "X-Goog-Drive-Resource-Keys": "FILE_ID/RESOURCE_ID",
                # Quick check to show we use `add_request_headers`
                "X-Abuse-Policy": Any.string(),
                "X-Complaints-To": Any.string(),
            },
            stream=True,
            timeout=10,
        )

        api._session.get.return_value.raise_for_status.assert_called_once_with()
        stream_bytes.assert_called_once_with(api._session.get.return_value)
        assert result == [0, 1, 2]

    def test_iter_file_accepts_resource_key(self, api):
        list(api.iter_file("FILE_ID", "SPECIFIED_RESOURCE_ID"))

        # pylint: disable=no-member,protected-access
        api._session.get.assert_called_once_with(
            url=Any(),
            headers=Any.dict.containing(
                {
                    "X-Goog-Drive-Resource-Keys": "FILE_ID/SPECIFIED_RESOURCE_ID",
                }
            ),
            stream=Any(),
            timeout=Any(),
        )

    def test_iter_file_handles_errors(self, api, stream_bytes):
        # We aren't going to go crazy here as `iter_handle_errors` is better
        # tested elsewhere
        def explode():
            raise TooManyRedirects("Request went wrong")

        stream_bytes.side_effect = (explode() for _ in range(1))

        with pytest.raises(UpstreamServiceError):
            list(api.iter_file(sentinel.file_id))

    @pytest.mark.parametrize("with_credentials", (True, False))
    def test_is_available(self, with_credentials):
        api = GoogleDriveAPI([sentinel.credentials] if with_credentials else None)

        assert api.is_available == with_credentials

    @pytest.mark.parametrize(
        "url,expected",
        (
            (
                "https://drive.google.com/uc?id=FILE_ID",
                {"file_id": "FILE_ID", "resource_key": None},
            ),
            (
                "https://drive.google.com/uc?Id=FILE_ID",
                {"file_id": "FILE_ID", "resource_key": None},
            ),
            (
                "https://drive.google.com/uc?id=FILE_ID&export=download",
                {"file_id": "FILE_ID", "resource_key": None},
            ),
            (
                "https://drive.google.com/uc?id=FILE_ID&export=download&resourceKey=RESOURCE_KEY",
                {"file_id": "FILE_ID", "resource_key": "RESOURCE_KEY"},
            ),
            (
                "https://drive.google.com/uc?id=FILE_ID&export=download&resourcekey=RESOURCE_KEY",
                {"file_id": "FILE_ID", "resource_key": "RESOURCE_KEY"},
            ),
            (
                "https://drive.google.com/uc?id=FILE_ID&export=download&via.open_sidebar=1&"
                "via.request_config_from_frame=https%3A%2F%2Flms.hypothes.is",
                {"file_id": "FILE_ID", "resource_key": None},
            ),
            (
                "https://drive.google.com/uc?id=FILE_ID&authuser=0&export=download",
                {"file_id": "FILE_ID", "resource_key": None},
            ),
            (
                "https://drive.google.com/u/1/uc?id=FILE_ID&export=download",
                {"file_id": "FILE_ID", "resource_key": None},
            ),
            (
                "https://drive.google.com/open?id=FILE_ID",
                {"file_id": "FILE_ID", "resource_key": None},
            ),
            (
                "https://drive.google.com/file/d/FILE_ID/view?usp=sharing&resourceKey=RESOURCE_KEY",
                {"file_id": "FILE_ID", "resource_key": "RESOURCE_KEY"},
            ),
            (
                "https://drive.google.com/file/d/FILE_ID/view",
                {"file_id": "FILE_ID", "resource_key": None},
            ),
            (
                "https://drive.google.com/a/su.edu/file/d/FILE_ID/view?usp=sharing",
                {"file_id": "FILE_ID", "resource_key": None},
            ),
            # Failure conditions
            ("https://drive.google.com/drive/u/0/folders/FOLDER_ID", None),
            ("https://drive.google.com/drive/u/0/folders/?id=FOLDER_ID", None),
            ("https://drive.google.com/drive/my-drive", None),
            ("https://drive.google.com/drive/priority?ths=true", None),
            ("https://not.google.com/uc?id=FILE_ID", None),
        ),
    )
    def test_parse_file_url(self, url, expected):
        assert GoogleDriveAPI.parse_file_url(url) == expected

    @pytest.fixture
    def api(self):
        return GoogleDriveAPI(
            credentials_list=[sentinel.credentials, sentinel.credentials_two],
            resource_keys={"FILE_ID": "RESOURCE_ID"},
        )

    @pytest.fixture(autouse=True)
    def stream_bytes(self, patch):
        return patch("via.services.google_drive.stream_bytes")

    @pytest.fixture(autouse=True)
    def AuthorizedSession(self, patch):
        return patch("via.services.google_drive.AuthorizedSession")

    @pytest.fixture(autouse=True)
    def Credentials(self, patch):
        return patch("via.services.google_drive.Credentials")
