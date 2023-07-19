from unittest.mock import sentinel

from via.services.youtube_api import Transcript, TranscriptText
from via.views.api.youtube import get_transcript


class TestGetTranscript:
    def test_it(self, pyramid_request, youtube_service):
        pyramid_request.matchdict.update(
            {"video_id": sentinel.video_id, "transcript_id": sentinel.transcript_id}
        )
        youtube_service.get_transcript.return_value = Transcript(
            track=sentinel.track,
            text=[
                TranscriptText(text="hello", start=1.2, duration=3.4),
                TranscriptText(text="there", start=5.6, duration=7.8),
            ],
        )

        response = get_transcript(pyramid_request)

        youtube_service.get_transcript.assert_called_once_with(
            video_id=sentinel.video_id, transcript_id=sentinel.transcript_id
        )
        assert response == {
            "data": {
                "type": "transcripts",
                "id": sentinel.video_id,
                "attributes": {
                    "segments": [
                        {"text": "hello", "start": 1.2, "duration": 3.4},
                        {"text": "there", "start": 5.6, "duration": 7.8},
                    ]
                },
            }
        }
