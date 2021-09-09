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
from pytest import param

from via.exceptions import BadURL, UnhandledUpstreamException, UpstreamServiceError
from via.views.exceptions import (
    EXCEPTION_MAP,
    google_drive_exceptions,
    other_exceptions,
)


class TestExceptionViews:
    @pytest.mark.parametrize(
        "exception_class,status_code",
        (
            param(
                HTTPUnsupportedMediaType,
                HTTPUnsupportedMediaType.code,
                id="Pyramid error",
            ),
            param(BlockingIOError, 500, id="Unknown python error"),
        ),
    )
    def test_values_are_copied_from_the_exception(
        self, exception_view, exception_class, status_code, pyramid_request
    ):
        exception = exception_class("details string")

        values = exception_view(exception, pyramid_request)

        assert values == Any.dict.containing(
            {
                "exception": Any.dict.containing(
                    {"class": exception.__class__.__name__, "details": "details string"}
                ),
                "status_code": status_code,
            }
        )

        assert pyramid_request.response.status_int == status_code

    @pytest.mark.parametrize(
        "exception_class,mapped_exception",
        (
            param(BadURL, BadURL, id="Mapped directly"),
            param(HTTPUnsupportedMediaType, HTTPClientError, id="Inherited"),
            param(BlockingIOError, UnhandledUpstreamException, id="Unmapped"),
        ),
    )
    def test_we_fill_in_other_values_based_on_exception_lookup(
        self, exception_view, exception_class, mapped_exception, pyramid_request
    ):
        exception = exception_class("details string")

        values = exception_view(exception, pyramid_request)

        assert values["exception"] == Any.dict.containing(
            EXCEPTION_MAP[mapped_exception]
        )

    @pytest.mark.parametrize("doc_url", (sentinel.doc_url, None))
    def test_it_reads_the_urls_from_the_request(
        self, exception_view, pyramid_request, doc_url
    ):
        pyramid_request.GET["url"] = doc_url
        pyramid_request.url = sentinel.request_url

        values = exception_view(ValueError(), pyramid_request)

        assert values["url"] == {"original": doc_url, "retry": sentinel.request_url}

    @pytest.mark.parametrize(
        "exception_class,should_report",
        (
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
        "exception_class,should_report",
        (
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

    @pytest.fixture(params=[other_exceptions, google_drive_exceptions])
    def exception_view(self, request):
        return request.param

    @pytest.fixture
    def pyramid_request(self):
        return DummyRequest()

    @pytest.fixture(autouse=True)
    def h_pyramid_sentry(self, patch):
        return patch("via.views.exceptions.h_pyramid_sentry")
