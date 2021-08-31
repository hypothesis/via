from unittest.mock import sentinel

from via.views.google_drive import proxy_google_drive_file


class TestGetFileContent:
    def test_it(self, pyramid_request, secure_link_service, google_drive_api):
        pyramid_request.matchdict.update(
            {"file_id": sentinel.file_id, "token": sentinel.token}
        )

        response = proxy_google_drive_file(pyramid_request)

        assert response.headers["Content-Disposition"] == "inline"
        assert response.headers["Content-Type"] == "application/pdf"
        assert (
            response.headers["Cache-Control"]
            == "public, max-age=43200, stale-while-revalidate=86400"
        )

        google_drive_api.iter_file.assert_called_once_with(sentinel.file_id)
        assert response.app_iter == google_drive_api.iter_file.return_value
