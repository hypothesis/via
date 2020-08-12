from unittest.mock import create_autospec, sentinel

import pytest
from h_matchers import Any
from pyramid.testing import DummyRequest

from via.views.debug import debug_headers


class TestDebugHeaders:
    def test_it(self, pyramid_request):
        pyramid_request.headers = {"Key": "Value"}
        response = debug_headers(sentinel.context, pyramid_request)

        pyramid_request.route_url.assert_called_once_with("debug_headers")

        assert response.status_code == 200
        assert response.text == Any.string.containing(
            pyramid_request.route_url.return_value
        )
        assert response.text == Any.string.containing("Key")
        assert response.text == Any.string.containing("Value")

    def test_it_does_not_clean_headers_with_raw_true(
        self, pyramid_request, clean_headers, OrderedDict
    ):
        pyramid_request.GET["raw"] = "1"

        debug_headers(sentinel.context, pyramid_request)

        clean_headers.assert_not_called()
        OrderedDict.assert_called_once_with(pyramid_request.headers)

    def test_it_cleans_headers_with_raw_false(
        self, pyramid_request, clean_headers, OrderedDict
    ):
        pyramid_request.GET["raw"] = ""

        debug_headers(sentinel.context, pyramid_request)

        OrderedDict.assert_not_called()
        clean_headers.assert_called_once_with(pyramid_request.headers)

    @pytest.fixture
    def OrderedDict(self, patch):
        return patch("via.views.debug.OrderedDict")

    @pytest.fixture
    def clean_headers(self, patch):
        clean_headers = patch("via.views.debug.clean_headers")
        clean_headers.return_value = {"something": "JSON serialisable"}
        return clean_headers

    @pytest.fixture
    def pyramid_request(self):
        pyramid_request = DummyRequest()

        # `route_url` seems to go big time bonkers if you use the built in one
        pyramid_request.route_url = create_autospec(pyramid_request.route_url)
        pyramid_request.route_url.return_value = "ROUTE_URL"

        return pyramid_request
