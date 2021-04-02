class TestStatus:
    def test_get_front_page(self, test_app):
        response = test_app.get("/_status", status=200)

        assert response.content_type == "application/json"
        assert response.json == {"status": "okay"}
        assert (
            response.headers["Cache-Control"]
            == "max-age=0, must-revalidate, no-cache, no-store"
        )
