import pytest

pytestmark = pytest.mark.usefixtures("checkmate_pass")


class TestStatus:
    def test_it(self, test_app):
        response = test_app.get("/_status")

        assert response.json == {"status": "okay"}
        assert response.status_code == 200
