class RequestBasedException(Exception):
    """An exception based on a requests error."""

    def __init__(self, message, requests_err=None):
        super().__init__(message)

        self.request = requests_err.request if requests_err else None
        self.response = requests_err.response if requests_err else None

    def __str__(self):
        string = super().__str__()

        if self.response is None:
            return string

        # Log the details of the response. This goes to both Sentry and the
        # application's logs. It's helpful for debugging to know how the
        # external service responded.

        return " ".join(
            [
                part
                for part in [
                    f"{string}:",
                    str(self.response.status_code or ""),
                    self.response.reason,
                    self.response.text,
                ]
                if part
            ]
        )


class BadURL(RequestBasedException):
    """An invalid URL was discovered."""

    def __init__(self, message, requests_err=None, url=None):
        super().__init__(message, requests_err)
        self.url = url

    status_int = 400


class UpstreamServiceError(RequestBasedException):
    """Something went wrong when calling an upstream service."""

    status_int = 409


class UnhandledUpstreamException(UpstreamServiceError):
    """Something we did not plan for went wrong."""

    status_int = 417


class UpstreamTimeout(UpstreamServiceError):
    """We timed out waiting for an upstream service."""

    # "504 - Gateway Timeout" is the correct thing to raise, but this
    # will cause Cloudflare to intercept it:
    # https://support.cloudflare.com/hc/en-us/articles/115003011431-Troubleshooting-Cloudflare-5XX-errors#502504error
    # We're using "408 - Request Timeout" which is technically
    # incorrect as it implies the user took too long, but has good semantics
    status_int = 408


class GoogleDriveServiceError(UpstreamServiceError):
    """Something interesting happened in Google Drive.

    We often use the more generic versions, but if there's something of
    particular interest, we might raise this error.
    """

    def __init__(self, message, status_int, requests_err=None):
        super().__init__(message, requests_err=requests_err)

        self.status_int = status_int


class ConfigurationError(Exception):
    """The application configuration is malformed."""
