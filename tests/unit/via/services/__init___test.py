from unittest.mock import call, sentinel

import pytest

from via.exceptions import ConfigurationError
from via.services import create_google_api, load_injected_json


class TestLoadInjectedJSON:
    def test_it(self, settings, tmpdir):
        json_file = tmpdir / "data.json"
        json_file.write('{"a": 1}')

        data = load_injected_json(settings, "data.json")

        assert data == {"a": 1}

    @pytest.mark.parametrize("required", (True, False))
    def test_it_with_malformed_data(self, settings, tmpdir, required):
        json_file = tmpdir / "data.json"
        json_file.write("{malformed ...")

        with pytest.raises(ConfigurationError):
            load_injected_json(settings, "data.json", required=required)

    def test_it_with_missing_data(self, settings):
        with pytest.raises(ConfigurationError):
            load_injected_json(settings, "missing.json")

    def test_it_with_missing_but_not_required_data(self, settings):
        assert load_injected_json(settings, "missing.json", required=False) is None

    @pytest.fixture
    def settings(self, tmpdir):
        return {"data_directory": tmpdir}


class TestCreateGoogleAPI:
    def test_it_with_credentials(
        self, pyramid_request, GoogleDriveAPI, load_injected_json
    ):
        load_injected_json.side_effect = (
            sentinel.credentials_list,
            sentinel.resource_keys,
        )
        settings = {"google_drive_in_python": True, "noise": "other"}

        api = create_google_api(settings)

        load_injected_json.assert_has_calls(
            [
                call(settings, "google_drive_credentials.json"),
                call(settings, "google_drive_resource_keys.json", required=False),
            ]
        )

        GoogleDriveAPI.assert_called_once_with(
            credentials_list=sentinel.credentials_list,
            resource_keys=sentinel.resource_keys,
        )
        assert api == GoogleDriveAPI.return_value

    def test_it_without_credentials(self, pyramid_request, GoogleDriveAPI):
        settings = {"google_drive_in_python": False, "noise": "other"}

        api = create_google_api(settings)

        GoogleDriveAPI.assert_called_once_with(credentials_list=None)
        assert api == GoogleDriveAPI.return_value

    @pytest.fixture(autouse=True)
    def load_injected_json(self, patch):
        return patch("via.services.load_injected_json")

    @pytest.fixture(autouse=True)
    def GoogleDriveAPI(self, patch):
        return patch("via.services.GoogleDriveAPI")
