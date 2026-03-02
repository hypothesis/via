def test_index_shows_page_when_not_signed_urls_required(test_app):
    """When signed_urls_required is False (default test config), index page is served."""
    response = test_app.get("/")

    assert response.status_code == 200
    # The normal index page is shown (not restricted) because
    # signed_urls_required=False means all requests are considered valid.
    assert "hypothes.is" in response.text
