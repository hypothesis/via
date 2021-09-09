import pytest
from requests import exceptions

from via.exceptions import (
    BadURL,
    UnhandledUpstreamException,
    UpstreamServiceError,
    UpstreamTimeout,
)
from via.requests_tools.error_handling import handle_errors, iter_handle_errors

EXCEPTION_MAP = (
    (exceptions.MissingSchema, BadURL),
    (exceptions.InvalidSchema, BadURL),
    (exceptions.InvalidURL, BadURL),
    (exceptions.URLRequired, BadURL),
    (exceptions.Timeout, UpstreamTimeout),
    (exceptions.ConnectionError, UpstreamServiceError),
    (exceptions.TooManyRedirects, UpstreamServiceError),
    (exceptions.SSLError, UpstreamServiceError),
    (exceptions.UnrewindableBodyError, UnhandledUpstreamException),
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
        self, iter_raiser, request_exception, expected_exception
    ):
        with pytest.raises(expected_exception):
            list(iter_raiser(request_exception("Oh noe")))

    def test_it_matches_custom_exceptions(self, iter_raiser):
        with pytest.raises(NotADirectoryError):
            list(iter_raiser(FileNotFoundError("Oh noe")))

    def test_it_does_not_catch_regular_exceptions(self, iter_raiser):
        with pytest.raises(ValueError):
            list(iter_raiser(ValueError()))

    @pytest.fixture
    def iter_raiser(self):
        def error_mapper(err):
            if isinstance(err, FileNotFoundError):
                return NotADirectoryError("Translated")

            return None

        @iter_handle_errors(error_mapper)
        def iter_raiser(exception):
            yield 1
            raise exception

        return iter_raiser
