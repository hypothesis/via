class TestRouteByContent:
    def test_route_shows_restricted_page(self, test_app):
        target_url = "http://example.com"

        response = test_app.get(f"/route?url={target_url}")

        assert response.status_code == 200
        assert "Access to Via is now restricted" in response.text
        assert target_url in response.text
