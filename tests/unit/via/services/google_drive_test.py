import json
from io import BytesIO
from unittest.mock import call, sentinel

import httplib2
import pytest
from googleapiclient.errors import HttpError
from h_matchers import Any
from pyramid.httpexceptions import HTTPNotFound

from via.exceptions import ConfigurationError, UpstreamServiceError
from via.services import GoogleDriveAPI
from via.services.google_drive import factory


def build_http_exception(status_code, message=None):
    """Create one of Googles annoying error classes."""

    # This is accurate to the 404 I received testing the real service, but
    # I've no idea if it represents other codes well.
    content = (
        json.dumps(
            {
                "error": {
                    "errors": [{"message": message}],
                    "code": status_code,
                    "message": message,
                }
            }
        ).encode("utf-8")
        if message
        else b""
    )

    return HttpError(httplib2.Response({"status": status_code}), content=content)


class TestGoogleDriveAPI:
    def test_it_builds_a_service_as_we_expect(self, Credentials, build):
        api = GoogleDriveAPI(sentinel.credentials)

        Credentials.from_service_account_info.assert_called_once_with(
            sentinel.credentials, scopes=GoogleDriveAPI.SCOPES
        )
        build.assert_called_once_with(
            "drive",
            "v3",
            credentials=Credentials.from_service_account_info.return_value,
        )
        # pylint: disable=protected-access
        assert api._service == build.return_value

    def test_it_with_bad_credentials(self, Credentials):
        # Google seems to raise plain ValueError's for bad config
        Credentials.from_service_account_info.side_effect = ValueError

        with pytest.raises(ConfigurationError):
            GoogleDriveAPI(sentinel.bad_credentials)

    def test_from_credentials_file_with_no_file(self):
        with pytest.raises(FileNotFoundError):
            GoogleDriveAPI.from_credentials_file("/missing/file")

    def test_from_credentials_file(self, tmpdir, Credentials):
        json_file = tmpdir / "credentials.json"
        json_file.write(json.dumps([{"credentials": 1}]))

        api = GoogleDriveAPI.from_credentials_file(json_file)

        Credentials.from_service_account_info.assert_called_once_with(
            {"credentials": 1}, scopes=GoogleDriveAPI.SCOPES
        )
        assert isinstance(api, GoogleDriveAPI)

    def test_iter_file(self, MediaIoBaseDownload):
        # This is all a bit black box, we don't necessarily know what all these
        # Google objects do, so we'll just check we call them in the right way
        api = GoogleDriveAPI(sentinel.credentials)
        MediaIoBaseDownload.return_value.next_chunk.side_effect = [
            (sentinel.status, False),
            (sentinel.status, False),
            (sentinel.status, True),
        ]

        result = list(api.iter_file(sentinel.file_id))

        # pylint: disable=no-member,protected-access
        api._service.files.assert_called_once_with()
        api._service.files.return_value.get_media.assert_called_once_with(
            fileId=sentinel.file_id
        )
        MediaIoBaseDownload.assert_called_once_with(
            Any.instance_of(BytesIO),
            api._service.files.return_value.get_media.return_value,
        )

        MediaIoBaseDownload.return_value.next_chunk.assert_has_calls(
            [call(), call(), call()]
        )

        # There's no content here, because our mock doesn't add to the bytes
        # object. But we can check we do get the bytes back
        assert result == [b"", b"", b""]

    @pytest.mark.parametrize(
        "code,expected_exception",
        (
            (404, HTTPNotFound),
            (403, UpstreamServiceError),
            (500, UpstreamServiceError),
        ),
    )
    def test_iter_file_with_errors(self, MediaIoBaseDownload, code, expected_exception):
        api = GoogleDriveAPI(sentinel.credentials)
        MediaIoBaseDownload.return_value.next_chunk.side_effect = build_http_exception(
            code, "Some error message"
        )

        with pytest.raises(expected_exception):
            list(api.iter_file(sentinel.file_id))

    def test_download_with_malformed_error_from_google(self, MediaIoBaseDownload):
        # Check we don't rely on the specific shape of the error
        api = GoogleDriveAPI(sentinel.credentials)
        MediaIoBaseDownload.return_value.next_chunk.side_effect = build_http_exception(
            404, message=None
        )

        with pytest.raises(HTTPNotFound):
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

    @pytest.fixture(autouse=True)
    def build(self, patch):
        return patch("via.services.google_drive.build")

    @pytest.fixture(autouse=True)
    def Credentials(self, patch):
        return patch("via.services.google_drive.Credentials")

    @pytest.fixture(autouse=True)
    def MediaIoBaseDownload(self, patch):
        return patch("via.services.google_drive.MediaIoBaseDownload")


class TestFactory:
    def test_it_with_credentials(self, pyramid_request, GoogleDriveAPI):
        pyramid_request.registry.settings[
            "google_drive_credentials_file"
        ] = sentinel.credentials_file

        api = factory(sentinel.context, pyramid_request)

        GoogleDriveAPI.from_credentials_file.assert_called_once_with(
            sentinel.credentials_file
        )
        assert api == GoogleDriveAPI.from_credentials_file.return_value

    def test_it_without_credentials(self, pyramid_request, GoogleDriveAPI):
        pyramid_request.registry.settings["google_drive_credentials_file"] = None

        api = factory(sentinel.context, pyramid_request)

        GoogleDriveAPI.assert_called_once_with(service_account_info=None)
        assert api == GoogleDriveAPI.return_value

    @pytest.fixture(autouse=True)
    def GoogleDriveAPI(self, patch):
        return patch("via.services.google_drive.GoogleDriveAPI")
