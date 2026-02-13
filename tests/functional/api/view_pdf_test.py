class TestViewPDFAPI:
    def test_pdf_shows_restricted_page(self, test_app):
        response = test_app.get("/pdf?url=http://example.com/foo.pdf")

        assert response.status_code == 200
        assert "Access to Via is now restricted" in response.text
        assert "http://example.com/foo.pdf" in response.text
