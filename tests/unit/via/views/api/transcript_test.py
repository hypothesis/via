from via.views.api.transcript import get_transcript


class TestGetTranscript:
    def test_it(self, pyramid_request, transcript_service):
        url = "https://example.com/transcript.vtt"
        pyramid_request.params["url"] = url

        response = get_transcript(pyramid_request)

        transcript_service.get_transcript.assert_called_once_with(url)
        assert response == {
            "data": {
                "type": "transcripts",
                "attributes": {
                    "segments": transcript_service.get_transcript.return_value
                },
            }
        }
