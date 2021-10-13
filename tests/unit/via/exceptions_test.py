import pytest
from requests.exceptions import HTTPError

from tests.common.requests_exceptions import make_requests_exception
from via.exceptions import RequestBasedException


class TestRequestBasedException:
    @pytest.mark.parametrize(
        "error_params,expected_string",
        (
            (
                {
                    "status_code": 400,
                    "reason": "Bad request",
                    "json_data": {"test": "data", "more": "data"},
                },
                'message: 400 Bad request {"test": "data", "more": "data"}',
            ),
            (
                {
                    "status_code": 401,
                    "raw_data": "<html>HTML response text!</html>",
                },
                "message: 401 <html>HTML response text!</html>",
            ),
            (
                {
                    "status_code": 402,
                },
                "message: 402",
            ),
        ),
    )
    def test_it(self, error_params, expected_string):
        exception = RequestBasedException(
            "message", requests_err=make_requests_exception(HTTPError, **error_params)
        )

        assert str(exception) == expected_string
