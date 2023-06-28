import logging
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

    def test_it_handles_errors_from_youtube(
        self, caplog, pyramid_request, youtube_service, report_exception_to_sentry
    ):
        exception = youtube_service.get_transcript.side_effect = RuntimeError(
            "Test error"
        )

        response = youtube.get_transcript(pyramid_request)

        report_exception_to_sentry.assert_called_once_with(exception)
        assert caplog.record_tuples == [
            ("via.views.api.youtube", logging.ERROR, str(exception))
        ]
        assert pyramid_request.response.status_int == 500
        assert response == {
            "errors": [
                {
                    "status": 500,
                    "code": "RuntimeError",
                    "title": "Failed to get transcript from YouTube",
                    "detail": str(exception).strip(),
                }
            ]
        }

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict["video_id"] = sentinel.video_id
        return pyramid_request


@pytest.fixture(autouse=True)
def report_exception_to_sentry(patch):
    return patch("via.views.api.youtube.report_exception_to_sentry")
