import pytest
from checkmatelib import CheckmateException

from via.views.status import get_status


class TestStatusRoute:
    @pytest.mark.parametrize(
        "include_checkmate,checkmate_fails,expected_status,expected_body",
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
    ):
        if include_checkmate:
            pyramid_request.params["include-checkmate"] = ""

        if checkmate_fails:
            pyramid_request.checkmate.check_url.side_effect = CheckmateException

        result = get_status(pyramid_request)

        assert pyramid_request.response.status_int == expected_status
        assert result == expected_body
