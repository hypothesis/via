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

    def test_it_with_malformed_data(self, settings, tmpdir):
        json_file = tmpdir / "data.json"
        json_file.write("{malformed ...")

        with pytest.raises(ConfigurationError):
            load_injected_json(settings, "data.json")

    def test_it_with_missing_data(self, settings):
        with pytest.raises(ConfigurationError):
            load_injected_json(settings, "missing.json")

    @pytest.fixture
    def settings(self, tmpdir):
        return {"data_directory": tmpdir}


class TestCreateGoogleAPI:
    def test_it_with_credentials(self, GoogleDriveAPI, load_injected_json):
        load_injected_json.side_effect = (
            sentinel.credentials_list,
            sentinel.resource_keys,
        )

        api = create_google_api(sentinel.settings)

        load_injected_json.assert_has_calls(
            [
                call(sentinel.settings, "google_drive_credentials.json"),
                call(sentinel.settings, "google_drive_resource_keys.json"),
            ]
        )

        GoogleDriveAPI.assert_called_once_with(
            credentials_list=sentinel.credentials_list,
            resource_keys=sentinel.resource_keys,
        )
        assert api == GoogleDriveAPI.return_value

    @pytest.fixture(autouse=True)
    def load_injected_json(self, patch):
        return patch("via.services.load_injected_json")

    @pytest.fixture(autouse=True)
    def GoogleDriveAPI(self, patch):
        return patch("via.services.GoogleDriveAPI")
