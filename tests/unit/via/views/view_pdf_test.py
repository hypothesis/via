from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPNoContent

from via.resources import QueryURLResource
from via.views.view_pdf import proxy_google_drive_file, view_pdf


@pytest.mark.usefixtures(
    "secure_link_service",
    "google_drive_api",
    "http_service",
    "pdf_url_builder_service",
)
class TestViewPDF:
    def test_it(self, call_view, pyramid_request, pyramid_settings, Configuration):
        response = call_view("http://example.com/foo.pdf")

        Configuration.extract_from_params.assert_called_once_with(
            pyramid_request.params
        )
        pyramid_request.checkmate.raise_if_blocked(sentinel.url)

        assert response == {
            "pdf_url": "http://example.com/foo.pdf",
            "proxy_pdf_url": Any(),
            "client_embed_url": pyramid_settings["client_embed_url"],
            "static_url": pyramid_request.static_url,
            "hypothesis_config": sentinel.h_config,
        }

    def test_it_builds_the_url_if_not_google(
        self, call_view, google_drive_api, pdf_url_builder_service
    ):
        google_drive_api.parse_file_url.return_value = None

        call_view("https://example.com/foo/bar.pdf?q=s")

        pdf_url_builder_service.get_pdf_url.assert_called_once_with(
            "https://example.com/foo/bar.pdf?q=s"
        )

    def test_it_builds_the_url_if_google(
        self,
        call_view,
        pdf_url_builder_service,
    ):
        url = "http://gdrive/document.pdf"

        response = call_view(url)

        pdf_url_builder_service.get_pdf_url.assert_called_once_with(url)
        assert (
            response["proxy_pdf_url"]
            == pdf_url_builder_service.get_pdf_url.return_value
        )

    def test_it_builds_the_url_if_ms_one_drive(
        self, call_view, pdf_url_builder_service
    ):
        url = "http://ms_one_drive_url/document.pdf"

        response = call_view(url)

        pdf_url_builder_service.get_pdf_url.assert_called_once_with(url)
        assert (
            response["proxy_pdf_url"]
            == pdf_url_builder_service.get_pdf_url.return_value
        )

    @pytest.fixture
    def Configuration(self, patch):
        Configuration = patch("via.views.view_pdf.Configuration")
        Configuration.extract_from_params.return_value = (
            sentinel.via_config,
            sentinel.h_config,
        )

        return Configuration

    @pytest.fixture(autouse=True)
    def google_drive_api(self, google_drive_api):
        google_drive_api.parse_file_url.return_value = None

        return google_drive_api


@pytest.mark.usefixtures(
    "secure_link_service", "google_drive_api", "pdf_url_builder_service"
)
class TestProxyGoogleDriveFile:
    def test_status_and_headers(
        self, pyramid_request, secure_link_service, google_drive_api
    ):
        response = proxy_google_drive_file(pyramid_request)

        assert response.status_code == 200
        assert response.headers["Content-Disposition"] == "inline"
        assert response.headers["Content-Type"] == "application/pdf"
        assert (
            response.headers["Cache-Control"]
            == "public, max-age=43200, stale-while-revalidate=86400"
        )

    def test_it_steams_content(self, pyramid_request, google_drive_api):
        # Create a generator and a counter of how many times it's been accessed
        def count_access(i):
            count_access.value += 1
            return i

        count_access.value = 0

        google_drive_api.iter_file.return_value = (count_access(i) for i in range(3))

        response = proxy_google_drive_file(pyramid_request)

        # The first and only the first item has been reified from the generator
        assert count_access.value == 1
        # And we still get everything if we iterate
        assert list(response.app_iter) == [0, 1, 2]

    def test_it_can_stream_an_empty_iterator(self, pyramid_request, google_drive_api):
        google_drive_api.iter_file.return_value = iter([])

        response = proxy_google_drive_file(pyramid_request)

        assert isinstance(response, HTTPNoContent)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict.update(
            {"file_id": sentinel.file_id, "token": sentinel.token}
        )

        return pyramid_request


@pytest.fixture
def call_view(pyramid_request):
    def call_view(url="http://example.com/name.pdf", params=None, view=view_pdf):
        pyramid_request.params = dict(params or {}, url=url)
        context = QueryURLResource(pyramid_request)
        return view(context, pyramid_request)

    return call_view
