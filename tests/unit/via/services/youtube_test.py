from unittest.mock import create_autospec, sentinel

import pytest

from via.exceptions import BadURL
from via.services.youtube import YouTubeService, YouTubeServiceError, factory
from via.services.youtube_api import YouTubeAPIClient


class TestYouTubeService:
    @pytest.mark.parametrize(
        "enabled,api_client,expected",
        [
            (False, None, False),
            (True, None, False),
            (False, sentinel.api_client, False),
            (True, sentinel.api_client, True),
        ],
    )
    def test_enabled(self, enabled, api_client, expected):
        assert (
            YouTubeService(enabled=enabled, api_client=api_client).enabled == expected
        )

    @pytest.mark.parametrize(
        "url,expected_video_id",
        [
            ("not_an_url", None),
            ("https://notyoutube:1000000", None),
            ("https://notyoutube.com", None),
            ("https://youtube.com", None),
            ("https://youtube.com?param=nope", None),
            ("https://youtube.com?v=", None),
            ("https://youtu/VIDEO_ID", None),
            ("https://youtube.com?v=VIDEO_ID", "VIDEO_ID"),
            ("https://www.youtube.com/watch?v=VIDEO_ID", "VIDEO_ID"),
            ("https://www.youtube.com/watch?v=VIDEO_ID&t=14s", "VIDEO_ID"),
            (
                "https://www.youtube.com/v/VIDEO_ID?fs=1&amp;hl=en_US&amp;rel=0",
                "VIDEO_ID",
            ),
            ("https://www.youtube.com/embed/VIDEO_ID?rel=0", "VIDEO_ID"),
            ("https://youtu.be/VIDEO_ID", "VIDEO_ID"),
            ("https://youtube.com/shorts/VIDEO_ID?feature=share", "VIDEO_ID"),
            ("https://www.youtube.com/live/VIDEO_ID?feature=share", "VIDEO_ID"),
            ("https://m.youtube.com/watch?v=VIDEO_ID", "VIDEO_ID"),
        ],
    )
    def test_get_video_id(self, url, expected_video_id, svc):
        assert expected_video_id == svc.get_video_id(url)

    @pytest.mark.parametrize(
        "kwargs",
        (
            {"video_url": "https://www.youtube.com/watch?v=VIDEO_ID"},
            {"video_id": "VIDEO_ID"},
        ),
    )
    def test_get_video_info(self, svc, api_client, kwargs):
        video = svc.get_video_info(with_captions=sentinel.with_captions, **kwargs)

        api_client.get_video_info.assert_called_once_with(
            video_id="VIDEO_ID", with_captions=sentinel.with_captions
        )

        assert video == api_client.get_video_info.return_value

    def test_get_video_info_with_bad_url(self, svc):
        with pytest.raises(BadURL):
            svc.get_video_info(video_url="BAD URL")

    def test_get_transcript(self, svc, api_client, CaptionTrack):
        transcript = svc.get_transcript(
            video_id=sentinel.video_id, transcript_id=sentinel.transcript_id
        )

        # This is called via `get_video_info`
        api_client.get_video_info.assert_called_once_with(
            sentinel.video_id, with_captions=True
        )
        video = api_client.get_video_info.return_value

        CaptionTrack.from_id.assert_called_once_with(sentinel.transcript_id)
        video.caption.find_matching_track.assert_called_once_with(
            [CaptionTrack.from_id.return_value]
        )
        caption_track = video.caption.find_matching_track.return_value

        api_client.get_transcript.assert_called_once_with(caption_track)
        assert transcript == api_client.get_transcript.return_value

    def test_get_transcript_with_no_matching_captions(self, svc, api_client):
        video = api_client.get_video_info.return_value
        video.caption.find_matching_track.return_value = None

        with pytest.raises(YouTubeServiceError):
            svc.get_transcript(video_id=sentinel.video_id, transcript_id="en")

    @pytest.fixture
    def api_client(self):
        return create_autospec(YouTubeAPIClient, spec_set=True, instance=True)

    @pytest.fixture
    def svc(self, api_client):
        return YouTubeService(enabled=True, api_client=api_client)

    @pytest.fixture
    def CaptionTrack(self, patch):
        return patch("via.services.youtube.CaptionTrack")


class TestFactory:
    def test_it(self, YouTubeService, YouTubeAPIClient, pyramid_request):
        svc = factory(sentinel.context, pyramid_request)

        YouTubeAPIClient.assert_called_once_with(api_key="test_youtube_api_key")
        YouTubeService.assert_called_once_with(
            enabled=True,
            api_client=YouTubeAPIClient.return_value,
        )
        assert svc == YouTubeService.return_value

    @pytest.fixture
    def YouTubeAPIClient(self, patch):
        return patch("via.services.youtube.YouTubeAPIClient")

    @pytest.fixture
    def YouTubeService(self, patch):
        return patch("via.services.youtube.YouTubeService")
