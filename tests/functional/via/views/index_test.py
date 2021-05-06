import pytest

from tests.functional.matchers import temporary_redirect_to


@pytest.mark.parametrize(
    "url,expected_redirect_location",
    [
        # When you submit the form on the front page it redirects you to the
        # page that will proxy the URL that you entered.
        (
            "https://example.com/foo/",
            "http://localhost/https://example.com/foo/",
        ),
        (
            "http://example.com/foo/",
            "http://localhost/http://example.com/foo/",
        ),
        # The submitted URL is normalized to strip leading/trailing spaces and
        # add a protocol.
        (
            "example.com/foo/",
            "http://localhost/https://example.com/foo/",
        ),
        # If you submit an empty form it just reloads the front page again.
        ("", "http://localhost/"),
    ],
)
def test_index(test_app, url, expected_redirect_location):
    form = test_app.get("/").form

    form.set("url", url)
    response = form.submit()

    assert response == temporary_redirect_to(expected_redirect_location)
