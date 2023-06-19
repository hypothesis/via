import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPNotFound

from via.views.api import youtube


class TestTranscript:
    def test_it(self, pyramid_request):
        response = youtube.transcript(pyramid_request)

        assert response == {
            "data": {
                "type": "transcripts",
                "id": "1",
                "attributes": {"segments": Any.list()},
            }
        }

    def test_it_errors_if_the_video_id_is_unknown(self, pyramid_request):
        pyramid_request.matchdict["video_id"] = "unknown"

        with pytest.raises(HTTPNotFound):
            youtube.transcript(pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict["video_id"] = "1"
        return pyramid_request
