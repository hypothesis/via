import json
from io import BytesIO
from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pyramid.httpexceptions import (
    HTTPClientError,
    HTTPGatewayTimeout,
    HTTPNotFound,
    HTTPUnsupportedMediaType,
)
from pyramid.testing import DummyRequest
from pytest import param  # noqa: PT013
from requests import HTTPError, Request, Response

from via.exceptions import (
    BadURL,
    GoogleDriveServiceError,
    UnhandledUpstreamException,
    UpstreamServiceError,
)
from via.views.exceptions import (
    EXCEPTION_MAP,
    google_drive_exceptions,
    other_exceptions,
)


class TestOtherExceptions:
    @pytest.mark.parametrize(
        "exception_class,status_code",  # noqa: PT006
        (  # noqa: PT007
            param(
                HTTPUnsupportedMediaType,
                HTTPUnsupportedMediaType.code,
                id="Pyramid error",
            ),
            param(BlockingIOError, 500, id="Unknown python error"),
        ),
    )
    def test_values_are_copied_from_the_exception(
        self, exception_class, status_code, pyramid_request
    ):
        exception = exception_class("details string")

        values = other_exceptions(exception, pyramid_request)

        assert values == Any.dict().containing(
            {
                "exception": Any.dict().containing(
                    {"class": exception.__class__.__name__, "details": "details string"}
                ),
                "status_code": status_code,
            }
        )

        assert pyramid_request.response.status_int == status_code

    @pytest.mark.parametrize(
        "exception_class,mapped_exception",  # noqa: PT006
        (  # noqa: PT007
            param(BadURL, BadURL, id="Mapped directly"),
            param(HTTPUnsupportedMediaType, HTTPClientError, id="Inherited"),
            param(BlockingIOError, UnhandledUpstreamException, id="Unmapped"),
        ),
    )
    def test_we_fill_in_other_values_based_on_exception_lookup(
        self, exception_class, mapped_exception, pyramid_request
    ):
        exception = exception_class("details string")

        values = other_exceptions(exception, pyramid_request)

        assert values["exception"] == Any.dict().containing(
            EXCEPTION_MAP[mapped_exception]
        )

    def test_it_reads_the_urls_from_the_request(
        self, pyramid_request, get_original_url
    ):
        pyramid_request.url = sentinel.request_url

        values = other_exceptions(ValueError(), pyramid_request)

        get_original_url.assert_called_once_with(pyramid_request.context)
        assert values["url"] == {
            "original": get_original_url.return_value,
            "retry": sentinel.request_url,
        }

    def test_it_doesnt_read_the_url_if_the_request_has_no_context(
        self, pyramid_request, get_original_url
    ):
        # It seems we can get in the situation where Pyramid does not provide
        # a context attribute at all on the object
        delattr(pyramid_request, "context")

        values = other_exceptions(ValueError(), pyramid_request)

        get_original_url.assert_not_called()
        assert values["url"]["original"] is None

    @pytest.mark.parametrize(
        "exception_class,should_report",  # noqa: PT006
        (  # noqa: PT007
            (UpstreamServiceError, False),
            (UnhandledUpstreamException, False),
            (BadURL, False),
            (HTTPClientError, False),
            (ValueError, True),
            (HTTPGatewayTimeout, True),
        ),
    )
    def test_other_exceptions_reporting_to_sentry(
        self, pyramid_request, h_pyramid_sentry, exception_class, should_report
    ):
        exception = exception_class("Oh no")

        other_exceptions(exception, pyramid_request)

        if should_report:
            h_pyramid_sentry.report_exception.assert_called_once_with(exception)
        else:
            h_pyramid_sentry.report_exception.assert_not_called()

    @pytest.mark.parametrize(
        "exception_class,should_report",  # noqa: PT006
        (  # noqa: PT007
            (HTTPNotFound, False),
            (UnhandledUpstreamException, True),
            (BadURL, True),
            (HTTPClientError, True),
            (ValueError, True),
            (HTTPGatewayTimeout, True),
        ),
    )
    def test_google_drive_exceptions_reporting_to_sentry(
        self, pyramid_request, h_pyramid_sentry, exception_class, should_report
    ):
        exception = exception_class("Oh no")

        google_drive_exceptions(exception, pyramid_request)

        if should_report:
            h_pyramid_sentry.report_exception.assert_called_once_with(exception)
        else:
            h_pyramid_sentry.report_exception.assert_not_called()

    @pytest.fixture
    def pyramid_request(self):
        return DummyRequest()

    @pytest.fixture(autouse=True)
    def get_original_url(self, patch):
        return patch("via.views.exceptions.get_original_url")

    @pytest.fixture(autouse=True)
    def h_pyramid_sentry(self, patch):
        return patch("via.views.exceptions.h_pyramid_sentry")


class TestGoogleDriveExceptions:
    def test_it(self, pyramid_request):
        json_body = {"test": "info"}

        # Constructing requests exceptions is no fun...
        request = Request("GET", "http://example.com")
        response = Response()
        response.status_code = 502
        response.raw = BytesIO(json.dumps(json_body).encode("utf-8"))
        response.headers["Content-Type"] = "mime/type"

        exception = GoogleDriveServiceError(
            "message", 419, HTTPError(request=request, response=response)
        )

        result = google_drive_exceptions(exception, pyramid_request)

        assert result == {
            "exception": "GoogleDriveServiceError",
            "message": "message",
            "upstream": {
                "content_type": response.headers["Content-Type"],
                "json": json_body,
                "status_code": response.status_code,
                "url": request.url,
            },
        }

        json.dumps(result)  # Check we are serialisable

        assert pyramid_request.response.status_int == 419

    @pytest.mark.parametrize(
        "raw,expected_text", ((123456, "... cannot retrieve ..."), (None, ""))  # noqa: PT006, PT007
    )
    def test_it_with_bad_response(self, pyramid_request, raw, expected_text):
        response = Response()
        response.raw = raw
        exception = GoogleDriveServiceError(
            "message", 419, HTTPError(response=response)
        )

        result = google_drive_exceptions(exception, pyramid_request)

        assert result == {
            "exception": "GoogleDriveServiceError",
            "message": "message",
            "upstream": {
                "content_type": None,
                "status_code": None,
                "text": expected_text,
            },
        }

        json.dumps(result)  # Check we are serialisable

    def test_it_with_normal_exception(self, pyramid_request):
        result = google_drive_exceptions(ValueError("message"), pyramid_request)

        assert result == {"exception": "ValueError", "message": "message"}

    def test_it_with_an_exception_with_a_non_string_arg(self, pyramid_request):
        exception = ValueError(set("a"))

        result = google_drive_exceptions(exception, pyramid_request)

        json.dumps(result)  # Check we are serialisable
