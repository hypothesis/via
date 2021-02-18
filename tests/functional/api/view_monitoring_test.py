import pytest

from tests.conftest import assert_cache_control


class TestViewMonitoring:
    def test_status_view(self, test_app):
        response = test_app.get("/_status")

        assert response.json == {"status": "okay"}
        assert response.status_code == 200
