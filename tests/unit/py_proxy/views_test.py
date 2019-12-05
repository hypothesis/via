from py_proxy import views


class TestIndexRoute:
    def test_index_renders_index_template(self, pyramid_request):
        result = views.index(pyramid_request)

        assert result == {}


class TestStatusRoute:
    def test_status_returns_200_response(self, pyramid_request):
        result = views.status(pyramid_request)

        assert result.status == "200 OK"
        assert result.status_int == 200
