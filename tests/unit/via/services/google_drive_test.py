import json
from unittest.mock import call, sentinel

import importlib_resources
import pytest
from h_matchers import Any
from marshmallow import ValidationError
from pyramid.httpexceptions import HTTPNotFound
from pytest import param
from requests import TooManyRedirects
from requests.exceptions import HTTPError, InvalidJSONError

from tests.common.requests_exceptions import make_requests_exception
from via.exceptions import (
    ConfigurationError,
    GoogleDriveServiceError,
    UnhandledUpstreamException,
    UpstreamServiceError,
)
from via.services.google_drive import (
    GoogleDriveAPI,
    GoogleDriveErrorSchema,
    _load_injected_json,
    factory,
)


def load_fixture(filename):
    ref = importlib_resources.files("tests.unit.via.services.fixtures").joinpath(
        filename
    )
    with ref.open(encoding="utf-8") as handle:
        return json.load(handle)


class TestGoogleErrorBodySchema:
    def test_it_returns_the_validated_data(self):
        json_data = {
            "error": {
                "errors": [
                    {
                        "reason": "notFound",
                        "message": "test_message",
                        "other": "foo",
                    },
                    {"another": "error"},
                ],
                "other": "foo",
            },
            "other": "foo",
        }

        assert GoogleDriveErrorSchema().load(json_data) == json_data

    @pytest.mark.parametrize(
        "json_data",
        [
            # The first error in the "errors" list not a dict.
            {"error": {"errors": [None]}},
            # No errors in the "errors" list.
            {"error": {"errors": []}},
            # The "errors" list not a list.
            {"error": {"errors": None}},
            # The "errors" list missing.
            {"error": {}},
            # The top-level "error" dict not a dict.
            {"error": 23},
            # The top-level "error" dict missing.
            {},
        ],
    )
    def test_it_raises_ValidationError_if_the_json_data_is_invalid(self, json_data):
        with pytest.raises(ValidationError):
            GoogleDriveErrorSchema().load(json_data)


class TestLoadInjectedJSON:
    def test_it(self, settings, tmpdir):
        json_file = tmpdir / "data.json"
        json_file.write('{"a": 1}')

        data = _load_injected_json(settings, "data.json")

        assert data == {"a": 1}

    def test_it_with_malformed_data(self, settings, tmpdir):
        json_file = tmpdir / "data.json"
        json_file.write("{malformed ...")

        with pytest.raises(ConfigurationError):
            _load_injected_json(settings, "data.json")

    def test_it_with_missing_data(self, settings):
        with pytest.raises(ConfigurationError):
            _load_injected_json(settings, "missing.json")

    @pytest.fixture
    def settings(self, tmpdir):
        return {"data_directory": tmpdir}


class TestFactory:
    def test_it_with_credentials(
        self, pyramid_request, GoogleDriveAPI, load_injected_json
    ):
        load_injected_json.side_effect = (
            sentinel.credentials_list,
            sentinel.resource_keys,
        )

        api = factory(sentinel.context, pyramid_request)

        load_injected_json.assert_has_calls(
            [
                call(
                    pyramid_request.registry.settings, "google_drive_credentials.json"
                ),
                call(
                    pyramid_request.registry.settings, "google_drive_resource_keys.json"
                ),
            ]
        )

        GoogleDriveAPI.assert_called_once_with(
            credentials_list=sentinel.credentials_list,
            resource_keys=sentinel.resource_keys,
        )
        assert api == GoogleDriveAPI.return_value

    @pytest.fixture(autouse=True)
    def load_injected_json(self, patch):
        return patch("via.services.google_drive._load_injected_json")

    @pytest.fixture(autouse=True)
    def GoogleDriveAPI(self, patch):
        return patch("via.services.google_drive.GoogleDriveAPI")


class TestGoogleDriveAPI:
    def test_it_builds_a_session_as_we_expect(
        self, api, Credentials, AuthorizedSession
    ):
        Credentials.from_service_account_info.assert_called_once_with(
            {"valid": "credentials"}, scopes=GoogleDriveAPI.SCOPES
        )
        AuthorizedSession.assert_called_once_with(
            Credentials.from_service_account_info.return_value,
            refresh_timeout=GoogleDriveAPI.TIMEOUT,
        )

    def test_it_with_bad_credentials(self, Credentials):
        # Google seems to raise plain ValueError's for bad config
        Credentials.from_service_account_info.side_effect = ValueError

        with pytest.raises(ConfigurationError):
            GoogleDriveAPI([{"invalid": "credentials"}], resource_keys={})

    def test_it_with_functest_credentials(self, AuthorizedSession):
        GoogleDriveAPI([{"disable": True}], resource_keys={})

        # In functest mode we don't finish building the object at all. So
        # attempting to use it should fail in a spectacular and obvious way
        AuthorizedSession.assert_not_called()

    def test_iter_file(self, api, AuthorizedSession):
        # This is all a bit black box, we don't necessarily know what all these
        # Google objects do, so we'll just check we call them in the right way
        list(api.iter_file("FILE_ID"))

        # pylint: disable=no-member,protected-access
        AuthorizedSession.return_value.request.assert_called_once_with(
            "GET",
            "https://www.googleapis.com/drive/v3/files/FILE_ID?alt=media",
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
            timeout=GoogleDriveAPI.TIMEOUT,
            max_allowed_time=GoogleDriveAPI.TIMEOUT,
        )

    def test_iter_file_accepts_resource_key(self, api, AuthorizedSession):
        list(api.iter_file("FILE_ID", "SPECIFIED_RESOURCE_ID"))

        # pylint: disable=no-member,protected-access
        AuthorizedSession.return_value.request.assert_called_once_with(
            "GET",
            Any(),
            headers=Any.dict.containing(
                {
                    "X-Goog-Drive-Resource-Keys": "FILE_ID/SPECIFIED_RESOURCE_ID",
                }
            ),
            stream=Any(),
            timeout=Any(),
            max_allowed_time=Any(),
        )

    def test_iter_file_handles_errors(self, api, AuthorizedSession):
        # We aren't going to go crazy here as `iter_handle_errors` is better
        # tested elsewhere
        def explode():
            raise TooManyRedirects("Request went wrong")

        AuthorizedSession.return_value.request.side_effect = (
            explode() for _ in range(1)
        )

        with pytest.raises(UpstreamServiceError):
            list(api.iter_file(sentinel.file_id))

    @pytest.mark.parametrize(
        "kwargs,error_class,status_code",
        (
            (
                {
                    "status_code": 404,
                    "json_data": load_fixture("google_404_file_not_found.json"),
                },
                HTTPNotFound,
                404,
            ),
            (
                {
                    "status_code": 403,
                    "json_data": load_fixture("google_403_rate_limited.json"),
                },
                GoogleDriveServiceError,
                429,
            ),
            (
                {
                    "status_code": 403,
                    "json_data": load_fixture("google_403_not_shared.json"),
                },
                GoogleDriveServiceError,
                403,
            ),
        ),
    )
    def test_iter_file_catches_specific_google_exceptions(
        self, api, kwargs, error_class, status_code, AuthorizedSession
    ):
        # pylint: disable=protected-access,line-too-long
        AuthorizedSession.return_value.request.return_value.raise_for_status.side_effect = make_requests_exception(
            HTTPError, **kwargs
        )

        with pytest.raises(error_class) as exception:
            list(api.iter_file(sentinel.file_id))

        assert exception.value.status_int == status_code

    @pytest.mark.parametrize(
        "kwargs",
        (
            param({"error_class": InvalidJSONError}, id="unexpected class"),
            param({"status_code": 503}, id="unexpected status code"),
            param({"json_data": None}, id="no json"),
            param({"raw_data": "{... broken}"}, id="malformed json"),
        ),
    )
    def test_iter_file_ignores_other_exceptions(self, api, AuthorizedSession, kwargs):
        attrs = {
            "error_class": HTTPError,
            "status_code": 404,
            "json_data": {"error": {"errors": [{"reason": "notFound"}]}},
        }
        attrs.update(kwargs)
        exception = make_requests_exception(**attrs)
        # pylint: disable=protected-access
        AuthorizedSession.return_value.request.return_value.raise_for_status.side_effect = (
            exception
        )

        with pytest.raises(UnhandledUpstreamException):
            list(api.iter_file(sentinel.file_id))

    def test_iter_file_has_no_issue_with_errors_without_responses(
        self, api, AuthorizedSession
    ):
        # pylint: disable=protected-access
        AuthorizedSession.return_value.request.return_value.raise_for_status.side_effect = (
            HTTPError()
        )
        with pytest.raises(UnhandledUpstreamException):
            list(api.iter_file(sentinel.file_id))

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
            credentials_list=[{"valid": "credentials"}, {"valid": "credentials_2"}],
            resource_keys={"FILE_ID": "RESOURCE_ID"},
        )

    @pytest.fixture(autouse=True)
    def AuthorizedSession(self, patch):
        return patch("via.services.google_drive.AuthorizedSession")

    @pytest.fixture(autouse=True)
    def Credentials(self, patch):
        return patch("via.services.google_drive.Credentials")
