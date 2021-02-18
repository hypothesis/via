from via.views.monitoring import get_status


class TestStatusRoute:
    def test_status_returns_200_response(self, make_request):
        request = make_request("/_status")

        result = get_status(request)

        assert result == {"status": "okay"}
