import pytest
from checkmatelib import CheckmateException

from via.views.status import status


class TestStatusRoute:
    @pytest.mark.parametrize(
        "include_checkmate,checkmate_fails,expected_status,expected_body",  # noqa: PT006
        [
            (False, False, 200, {"status": "okay"}),
            (False, True, 200, {"status": "okay"}),
            (True, False, 200, {"status": "okay", "okay": ["checkmate"]}),
            (True, True, 500, {"status": "down", "down": ["checkmate"]}),
        ],
    )
    def test_status_returns_200_response(
        self,
        pyramid_request,
        include_checkmate,
        checkmate_fails,
        expected_status,
        expected_body,
        checkmate_service,
        capture_message,
    ):
        if include_checkmate:
            pyramid_request.params["include-checkmate"] = ""

        if checkmate_fails:
            checkmate_service.check_url.side_effect = CheckmateException

        result = status(pyramid_request)

        assert pyramid_request.response.status_int == expected_status
        assert result == expected_body
        capture_message.assert_not_called()

    def test_status_sends_test_messages_to_sentry(
        self, pyramid_request, capture_message
    ):
        pyramid_request.params["sentry"] = ""

        status(pyramid_request)

        capture_message.assert_called_once_with("Test message from Via's status view")


@pytest.fixture(autouse=True)
def capture_message(patch):
    return patch("via.views.status.capture_message")
