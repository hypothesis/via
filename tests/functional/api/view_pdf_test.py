from tests.conftest import assert_cache_control


class TestViewPDFAPI:
    def test_caching_is_disabled(self, test_app):
        response = test_app.get("/pdf?url=http://example.com/foo.pdf")

        assert_cache_control(
            response.headers, ["max-age=0", "must-revalidate", "no-cache", "no-store"]
        )
