from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPClientError, HTTPUnsupportedMediaType
from pyramid.testing import DummyRequest
from pytest import param

from via.exceptions import BadURL, UnhandledException
from via.views.exceptions import EXCEPTION_MAP, all_exceptions


class TestErrorView:
    @pytest.mark.parametrize(
        "exception_class,status_code",
        (
            param(
                HTTPUnsupportedMediaType,
                HTTPUnsupportedMediaType.code,
                id="Pyramid error",
            ),
            param(BlockingIOError, 417, id="Unknown python error"),
        ),
    )
    def test_values_are_copied_from_the_exception(
        self, exception_class, status_code, pyramid_request
    ):
        exception = exception_class("details string")

        values = all_exceptions(exception, pyramid_request)

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
            param(BlockingIOError, UnhandledException, id="Unmapped"),
        ),
    )
    def test_we_fill_in_other_values_based_on_exception_lookup(
        self, exception_class, mapped_exception, pyramid_request
    ):
        exception = exception_class("details string")

        values = all_exceptions(exception, pyramid_request)

        assert values["exception"] == Any.dict.containing(
            EXCEPTION_MAP[mapped_exception]
        )

    @pytest.mark.parametrize("doc_url", (sentinel.doc_url, None))
    def test_it_reads_the_urls_from_the_request(self, pyramid_request, doc_url):
        pyramid_request.GET["url"] = doc_url
        pyramid_request.url = sentinel.request_url

        values = all_exceptions(ValueError(), pyramid_request)

        assert values["url"] == {"original": doc_url, "retry": sentinel.request_url}

    @pytest.fixture
    def pyramid_request(self):
        return DummyRequest()
