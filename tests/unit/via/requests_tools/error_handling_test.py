import pytest
from requests import exceptions

from via.exceptions import BadURL, UnhandledException, UpstreamServiceError
from via.requests_tools.error_handling import handle_errors, iter_handle_errors

EXCEPTION_MAP = (
    (exceptions.MissingSchema, BadURL),
    (exceptions.InvalidSchema, BadURL),
    (exceptions.InvalidURL, BadURL),
    (exceptions.URLRequired, BadURL),
    (exceptions.ConnectionError, UpstreamServiceError),
    (exceptions.Timeout, UpstreamServiceError),
    (exceptions.TooManyRedirects, UpstreamServiceError),
    (exceptions.SSLError, UpstreamServiceError),
    (exceptions.UnrewindableBodyError, UnhandledException),
)


class TestHandleErrors:
    @pytest.mark.parametrize("request_exception,expected_exception", EXCEPTION_MAP)
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


class TestIterHandleErrors:
    @pytest.mark.parametrize("request_exception,expected_exception", EXCEPTION_MAP)
    def test_it_catches_requests_exceptions(
        self, iter_raiser, request_exception, expected_exception, h_pyramid_sentry
    ):
        exception = request_exception("Oh noe")

        with pytest.raises(expected_exception):
            list(iter_raiser(exception))

        h_pyramid_sentry.report_exception.assert_called_once_with(exception)

    def test_it_does_not_catch_regular_exceptions(self, iter_raiser):
        with pytest.raises(ValueError):
            list(iter_raiser(ValueError()))

    @pytest.fixture
    def iter_raiser(self):
        @iter_handle_errors
        def iter_raiser(exception):
            yield 1
            raise exception

        return iter_raiser

    @pytest.fixture
    def h_pyramid_sentry(self, patch):
        return patch("via.requests_tools.error_handling.h_pyramid_sentry")
