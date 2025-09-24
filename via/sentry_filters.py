"""Functions for filtering out events and log messages we don't want to report to Sentry."""

from sentry_sdk.types import Hint, Log


def sentry_before_send_log(log: Log, _hint: Hint) -> Log | None:
    """Filter out log messages that we don't want to send to Sentry Logs."""

    if log.get("attributes", {}).get("logger.name") == "gunicorn.access":
        return None

    return log


SENTRY_FILTERS = []
