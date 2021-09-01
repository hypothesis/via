import pytest
from requests import exceptions

from via.exceptions import BadURL, UnhandledException, UpstreamServiceError
from via.requests_tools.error_handling import handle_errors


class TestHandleErrors:
    @pytest.mark.parametrize(
        "request_exception,expected_exception",
        (
            (exceptions.MissingSchema, BadURL),
            (exceptions.InvalidSchema, BadURL),
            (exceptions.InvalidURL, BadURL),
            (exceptions.URLRequired, BadURL),
            (exceptions.ConnectionError, UpstreamServiceError),
            (exceptions.Timeout, UpstreamServiceError),
            (exceptions.TooManyRedirects, UpstreamServiceError),
            (exceptions.SSLError, UpstreamServiceError),
            (exceptions.UnrewindableBodyError, UnhandledException),
        ),
    )
    def test_it_catches_requests_exceptions(
        self, raiser, request_exception, expected_exception
    ):
        with pytest.raises(expected_exception):
            raiser(request_exception("Oh noe"))

    def test_it_does_not_catch_regular_exceptions(self, raiser):
        with pytest.raises(ValueError):
            raiser(ValueError())

    @pytest.fixture
    def raiser(self):
        @handle_errors
        def raiser(exception):
            raise exception

        return raiser
