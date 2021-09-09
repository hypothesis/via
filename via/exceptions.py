class BadURL(Exception):
    """An invalid URL was discovered."""

    status_int = 400


class UpstreamServiceError(Exception):
    """Something went wrong when calling an upstream service."""

    status_int = 409


class UnhandledUpstreamException(Exception):
    """Something we did not plan for went wrong."""

    status_int = 417


class GoogleDriveServiceError(UpstreamServiceError):
    """Something interesting happened in Google Drive.

    We often use the more generic versions, but if there's something of
    particular interest, we might raise this error.
    """

    def __init__(self, message, error_json, status_int):
        self.error_json = error_json
        self.status_int = status_int

        super().__init__(message)


class ConfigurationError(Exception):
    """The application configuration is malformed."""
