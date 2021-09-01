from unittest.mock import sentinel

import pytest
from h_matchers import Any
from requests import TooManyRedirects

from via.exceptions import ConfigurationError, UpstreamServiceError
from via.services.google_drive import GoogleDriveAPI, factory


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
            GoogleDriveAPI(sentinel.bad_credentials)

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
                # Quick check to show we use `add_request_headers`
                "X-Abuse-Policy": Any.string(),
                "X-Complaints-To": Any.string(),
            },
            stream=True,
            timeout=1,
        )

        api._session.get.return_value.raise_for_status.assert_called_once_with()
        stream_bytes.assert_called_once_with(api._session.get.return_value)
        assert result == [0, 1, 2]

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
        api = GoogleDriveAPI(sentinel.credentials if with_credentials else None)

        assert api.is_available == with_credentials

    @pytest.mark.parametrize(
        "url,expected",
        (
            ("https://drive.google.com/uc?id=FILE_ID&export=download", "FILE_ID"),
            ("https://drive.google.com/uc?id=FILE_ID&export=download-MORE", None),
            ("https://drive.google.com/uc?id=FILE_ID", None),
            ("", None),
        ),
    )
    def test_google_drive_id(self, url, expected):
        assert GoogleDriveAPI.google_drive_id(url) == expected

    @pytest.fixture
    def api(self):
        return GoogleDriveAPI(sentinel.credentials)

    @pytest.fixture(autouse=True)
    def stream_bytes(self, patch):
        return patch("via.services.google_drive.stream_bytes")

    @pytest.fixture(autouse=True)
    def AuthorizedSession(self, patch):
        return patch("via.services.google_drive.AuthorizedSession")

    @pytest.fixture(autouse=True)
    def Credentials(self, patch):
        return patch("via.services.google_drive.Credentials")


class TestFactory:
    def test_it_with_credentials(self, pyramid_request, GoogleDriveAPI):
        pyramid_request.registry.settings.update(
            {
                "google_drive_credentials": '{"some": "json"}',
                "google_drive_in_python": True,
            }
        )

        api = factory(sentinel.context, pyramid_request)

        GoogleDriveAPI.assert_called_once_with({"some": "json"})
        assert api == GoogleDriveAPI.return_value

    def test_it_without_credentials(self, pyramid_request, GoogleDriveAPI):
        pyramid_request.registry.settings.update(
            {"google_drive_credentials": None, "google_drive_in_python": False}
        )

        api = factory(sentinel.context, pyramid_request)

        GoogleDriveAPI.assert_called_once_with(service_account_info=None)
        assert api == GoogleDriveAPI.return_value

    @pytest.mark.parametrize("credentials", ('{"malformed json....', None))
    def test_it_with_invalid_credentials(self, pyramid_request, credentials):
        pyramid_request.registry.settings.update(
            {"google_drive_credentials": credentials, "google_drive_in_python": True}
        )

        with pytest.raises(ConfigurationError):
            factory(sentinel.context, pyramid_request)

    @pytest.fixture(autouse=True)
    def GoogleDriveAPI(self, patch):
        return patch("via.services.google_drive.GoogleDriveAPI")
