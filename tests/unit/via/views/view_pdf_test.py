from unittest.mock import create_autospec, sentinel

import pytest

from via.resources import QueryURLResource
from via.views.view_pdf import proxy_google_drive_file, proxy_python_pdf, view_pdf


class TestViewPDF:
    def test_it_returns_restricted_page_with_target_url(self, call_view):
        response = call_view("http://example.com/foo.pdf")

        assert response == {"target_url": "http://example.com/foo.pdf"}

    def test_it_returns_none_target_url_on_error(self, context, pyramid_request):
        context.url_from_query.side_effect = Exception("bad url")

        result = view_pdf(context, pyramid_request)

        assert result == {"target_url": None}

    @pytest.fixture
    def context(self):
        return create_autospec(QueryURLResource, spec_set=True, instance=True)


class TestProxyGoogleDriveFile:
    def test_it_returns_restricted_page(self, pyramid_request):
        response = proxy_google_drive_file(pyramid_request)

        assert response == {"target_url": None}


class TestProxyPythonPDF:
    def test_it_returns_restricted_page_with_target_url(self, call_view):
        response = call_view("https://one-drive.com", view=proxy_python_pdf)

        assert response == {"target_url": "https://one-drive.com"}


@pytest.fixture
def call_view(pyramid_request):
    def call_view(url="http://example.com/name.pdf", params=None, view=view_pdf):
        pyramid_request.params = dict(params or {}, url=url)
        context = QueryURLResource(pyramid_request)
        return view(context, pyramid_request)

    return call_view
