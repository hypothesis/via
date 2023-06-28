from unittest.mock import sentinel

import pytest

from via.views.api import youtube


class TestGetTranscript:
    def test_it(self, pyramid_request, youtube_service):
        response = youtube.get_transcript(pyramid_request)

        youtube_service.get_transcript.assert_called_once_with(sentinel.video_id)
        assert response == {
            "data": {
                "type": "transcripts",
                "id": sentinel.video_id,
                "attributes": {"segments": youtube_service.get_transcript.return_value},
            }
        }

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict["video_id"] = sentinel.video_id
        return pyramid_request
