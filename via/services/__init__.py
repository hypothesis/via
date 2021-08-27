"""Services for Via."""
from via.services.google_drive import GoogleDriveAPI
from via.services.secure_link import SecureLinkService, has_secure_url_token
from via.services.via_client import ViaClientService


def includeme(config):  # pragma: no cover
    """Add services to pyramid config."""

    config.register_service_factory(
        "via.services.via_client.factory", iface=ViaClientService
    )
    config.register_service_factory(
        "via.services.google_drive.factory", iface=GoogleDriveAPI
    )
    config.register_service_factory(
        "via.services.secure_link.factory", iface=SecureLinkService
    )
