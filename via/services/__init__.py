"""Services for Via."""

from via.services.via_client import ViaClientService


def includeme(config):  # pragma: no cover
    """Add services to pyramid config."""

    config.register_service_factory(
        "via.services.via_client.factory", iface=ViaClientService
    )
