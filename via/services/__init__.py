"""Services for Via."""

import json
from json import JSONDecodeError
from pathlib import Path  # noqa: TC003

from via.exceptions import ConfigurationError
from via.services.checkmate import CheckmateService
from via.services.google_drive import GoogleDriveAPI
from via.services.http import HTTPService
from via.services.pdf_url import PDFURLBuilder
from via.services.secure_link import SecureLinkService, has_secure_url_token
from via.services.transcript import TranscriptService
from via.services.url_details import URLDetailsService
from via.services.via_client import ViaClientService
from via.services.youtube import YouTubeService
from via.services.youtube_transcript import YouTubeTranscriptService


def includeme(config):  # pragma: no cover
    """Add services to pyramid config."""

    config.register_service(
        create_google_api(config.registry.settings), iface=GoogleDriveAPI
    )

    config.register_service_factory(
        "via.services.checkmate.factory", iface=CheckmateService
    )
    config.register_service_factory(
        "via.services.via_client.factory", iface=ViaClientService
    )
    config.register_service_factory(
        "via.services.secure_link.factory", iface=SecureLinkService
    )
    config.register_service_factory("via.services.http.factory", iface=HTTPService)

    config.register_service_factory("via.services.pdf_url.factory", iface=PDFURLBuilder)

    config.register_service_factory(
        "via.services.transcript.factory", iface=TranscriptService
    )

    config.register_service_factory(
        "via.services.youtube.factory", iface=YouTubeService
    )
    config.register_service_factory(
        "via.services.youtube_transcript.factory", iface=YouTubeTranscriptService
    )

    config.register_service_factory(
        "via.services.url_details.factory", iface=URLDetailsService
    )


def create_google_api(settings):
    """Create from Pyramid settings."""

    return GoogleDriveAPI(
        credentials_list=load_injected_json(settings, "google_drive_credentials.json"),
        resource_keys=load_injected_json(settings, "google_drive_resource_keys.json"),
    )


def load_injected_json(settings, file_name):
    """Load a JSON file from the env specified `DATA_DIRECTORY`.

    This data is provided to us externally (by S3 at the moment) or any other
    mechanism which causes files to exist in the directory we expect.

    :param settings: A dict of Pyramid settings
    :param file_name: Filename to load
    :return: Decoded JSON data

    :raises ConfigurationError: If the file is required and not found or
        malformed
    """

    data_directory: Path = settings.get("data_directory")
    resource = data_directory / file_name

    if not resource.exists():
        raise ConfigurationError(f"Expected data file '{resource}' not found")  # noqa: EM102, TRY003

    with resource.open(encoding="utf-8") as handle:
        try:
            return json.load(handle)
        except JSONDecodeError as exc:
            raise ConfigurationError(f"Invalid data file format: '{resource}'") from exc  # noqa: EM102, TRY003
