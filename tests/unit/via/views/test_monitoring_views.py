from via.views.monitoring_views import get_status


class TestStatusRoute:
    def test_status_returns_200_response(self, make_pyramid_request):
        request = make_pyramid_request("/status")

        result = get_status(request)

        assert result.status == "200 OK"
        assert result.status_int == 200
