import logging

import pytest

from via.views.api.exceptions import APIExceptionViews


def test_exception(views, context, pyramid_request, report_exception_to_sentry, caplog):
    response = views.exception()

    report_exception_to_sentry.assert_called_once_with(context)
    assert caplog.record_tuples == [
        ("via.views.api.exceptions", logging.ERROR, str(context))
    ]
    assert pyramid_request.response.status_int == 500
    assert response == {
        "errors": [
            {
                "status": 500,
                "code": "RuntimeError",
                "title": "Something went wrong",
                "detail": str(context).strip(),
            }
        ]
    }


def test_exception_with_a_cause(views, context):
    context.cause = "The cause of the error"

    response = views.exception()

    assert response["errors"][0]["title"] == context.cause


def test_forbidden(views, pyramid_request):
    response = views.forbidden()

    assert pyramid_request.response.status_int == 403
    assert response is None


def test_notfound(views, pyramid_request):
    response = views.notfound()

    assert pyramid_request.response.status_int == 404
    assert response is None


@pytest.fixture
def context():
    return RuntimeError("Test error")


@pytest.fixture
def views(context, pyramid_request):
    return APIExceptionViews(context, pyramid_request)


@pytest.fixture(autouse=True)
def report_exception_to_sentry(patch):
    return patch("via.views.api.exceptions.report_exception_to_sentry")
