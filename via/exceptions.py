class BadURL(Exception):
    """An invalid URL was discovered."""

    status_int = 400


class UpstreamServiceError(Exception):
    """Something went wrong when calling an upstream service."""

    status_int = 409


class UnhandledUpstreamException(Exception):
    """Something we did not plan for went wrong."""

    status_int = 417


class ConfigurationError(Exception):
    """The application configuration is malformed."""
