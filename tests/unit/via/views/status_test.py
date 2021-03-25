import pytest
from checkmatelib import CheckmateException

from via.views.status import status


class TestStatus:
    def test_it_returns_200_response(self, make_request):
        request = make_request("/_status")

        result = status(request)

        assert result == {"status": "okay"}

    def test_it_reports_failure_if_calling_checkmate_fails(
        self, checkmate, make_request
    ):
        checkmate.check_url.side_effect = CheckmateException

        result = status(make_request("/_status"))

        assert result["status"] == "checkmate_failure"


@pytest.fixture
def checkmate(CheckmateClient):
    return CheckmateClient.return_value


@pytest.fixture(autouse=True)
def CheckmateClient(patch):
    return patch("via.views.status.CheckmateClient")
