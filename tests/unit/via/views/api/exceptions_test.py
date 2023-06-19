import pytest

from via.views.api.exceptions import APIExceptionViews


def test_forbidden(views, pyramid_request):
    response = views.forbidden()

    assert pyramid_request.response.status_int == 403
    assert response is None


def test_notfound(views, pyramid_request):
    response = views.notfound()

    assert pyramid_request.response.status_int == 404
    assert response is None


@pytest.fixture
def views(pyramid_request):
    return APIExceptionViews(pyramid_request)
