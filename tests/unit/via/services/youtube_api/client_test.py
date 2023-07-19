from unittest.mock import sentinel

import pytest

from via.services.youtube_api import (
    CaptionTrack,
    Transcript,
    TranscriptText,
    YouTubeAPIClient,
)


class TestYouTubeAPIClient:
    def test_get_video_info(self, client, http_session, Video):
        video = client.get_video_info("VIDEO_ID")

        http_session.post.assert_called_once_with(
            "https://youtubei.googleapis.com/youtubei/v1/player",
            json={
                "context": {
                    "client": {
                        "hl": "en",
                        "clientName": "WEB",
                        # Suspicious value right here...
                        "clientVersion": "2.20210721.00.00",
                    }
                },
                "videoId": "VIDEO_ID",
            },
        )
        response = http_session.post.return_value
        response.json.assert_called_once_with()

        Video.from_v1_json.assert_called_once_with(data=response.json.return_value)
        assert video == Video.from_v1_json.return_value

    def test_get_transcript(self, client, http_session):
        caption_track = CaptionTrack("en", base_url=sentinel.url)
        response = http_session.get.return_value
        response.text = """
        <transcript>
            <text start="0.21" dur="1.387">Hey there guys,</text>

            <text start="1.597">Lichen&#39; subscribe        </text>
            <text start="4.327" dur="2.063">
                &lt;font color=&quot;#A0AAB4&quot;&gt;Buy my merch!&lt;/font&gt;
            </text>
        </transcript>
        """

        transcript = client.get_transcript(caption_track)

        http_session.get.assert_called_once_with(url=caption_track.url)
        assert transcript == Transcript(
            track=caption_track,
            text=[
                TranscriptText(text="Hey there guys,", start=0.21, duration=1.387),
                TranscriptText(text="Lichen' subscribe", start=1.597, duration=0.0),
                TranscriptText(text="Buy my merch!", start=4.327, duration=2.063),
            ],
        )

    def test_get_transcript_with_no_url(self, client):
        with pytest.raises(ValueError):
            client.get_transcript(CaptionTrack("en", base_url=None))

    @pytest.fixture
    def client(self):
        return YouTubeAPIClient()

    @pytest.fixture
    def Video(self, patch):
        return patch("via.services.youtube_api.client.Video")

    @pytest.fixture(autouse=True)
    def http_session(self, patch):
        return patch("via.services.youtube_api.client.HTTPService").return_value
