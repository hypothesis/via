def test_index_shows_restricted_page(test_app):
    response = test_app.get("/")

    assert response.status_code == 200
    assert "Access to Via is now restricted" in response.text
