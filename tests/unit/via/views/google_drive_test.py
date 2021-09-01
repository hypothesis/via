from unittest.mock import sentinel

import pytest

from via.views.google_drive import proxy_google_drive_file


@pytest.mark.usefixtures("secure_link_service", "google_drive_api")
class TestGetFileContent:
    def test_it_adds_headers(
        self, pyramid_request, secure_link_service, google_drive_api
    ):
        response = proxy_google_drive_file(pyramid_request)

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

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict.update(
            {"file_id": sentinel.file_id, "token": sentinel.token}
        )

        return pyramid_request
