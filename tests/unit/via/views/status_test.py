from via.views.status import get_status


class TestStatusRoute:
    def test_status_returns_200_response(self, pyramid_request):
        result = get_status(pyramid_request)

        assert result == {"status": "okay"}
