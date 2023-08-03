from datetime import timedelta
from io import BytesIO
from unittest.mock import create_autospec, sentinel

import pytest
from h_matchers import Any
from requests import Response
from sqlalchemy import select

from via.models import Transcript, Video
from via.services import youtube_api
from via.services.youtube import (
    CAPTION_TRACK_PREFERENCES,
    YouTubeDataAPIError,
    YouTubeService,
    factory,
)
from via.services.youtube_api import YouTubeAPIClient


class TestYouTubeService:
    @pytest.mark.parametrize("enabled", (True, False))
    @pytest.mark.parametrize("api_key", (sentinel.api_key, None))
    def test_enabled(self, enabled, api_key):
        svc = YouTubeService(
            db_session=sentinel.db_session,
            enabled=enabled,
            api_client=sentinel.api_client,
            api_key=api_key,
            http_service=sentinel.http_service,
        )

        assert svc.enabled == bool(enabled and api_key)

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

    def test_get_video_title(self, svc, db_session, http_service):
        response = http_service.get.return_value = Response()
        response.raw = BytesIO(b'{"items": [{"snippet": {"title": "video_title"}}]}')

        title = svc.get_video_title("test_video_id")

        http_service.get.assert_called_once_with(
            "https://www.googleapis.com/youtube/v3/videos",
            params={
                "id": "test_video_id",
                "key": sentinel.api_key,
                "part": "snippet",
                "maxResults": "1",
            },
        )
        assert title == "video_title"
        # It should have cached the video in the DB.
        assert db_session.scalars(
            select(Video).where(Video.video_id == "test_video_id")
        ).all() == [Any.instance_of(Video).with_attrs({"title": "video_title"})]

    def test_get_video_title_uses_cached_videos(self, svc, http_service, video):
        title = svc.get_video_title(video.video_id)

        assert title == video.title
        http_service.get.assert_not_called()

    def test_get_video_title_raises_YouTubeDataAPIError(self, svc, http_service):
        http_service.get.side_effect = RuntimeError()

        with pytest.raises(YouTubeDataAPIError) as exc_info:
            svc.get_video_title("test_video_id")

        assert exc_info.value.__cause__ == http_service.get.side_effect

    def test_get_transcript_from_youtube(self, svc, db_session, youtube_api_client):
        transcript = youtube_api.Transcript(
            track=sentinel.track,
            text=[youtube_api.TranscriptText(text="text", start=1.0, duration=2.0)],
        )
        youtube_api_client.get_transcript.return_value = transcript
        video = youtube_api_client.get_video_info.return_value
        caption_track = video.caption.find_matching_track.return_value
        caption_track.id = "CAPTION_TRACK_ID"

        result = svc.get_transcript("VIDEO_ID")

        youtube_api_client.get_video_info.assert_called_once_with(video_id="VIDEO_ID")
        video.caption.find_matching_track.assert_called_once_with(
            CAPTION_TRACK_PREFERENCES
        )
        youtube_api_client.get_transcript.assert_called_once_with(caption_track)

        assert result == [{"text": "text", "start": 1.0, "duration": 2.0}]
        # It should have cached the transcript in the DB.
        assert db_session.scalars(select(Transcript)).all() == [
            Any.instance_of(Transcript).with_attrs(
                {
                    "video_id": "VIDEO_ID",
                    "transcript_id": "CAPTION_TRACK_ID",
                    "transcript": [{"text": "text", "start": 1.0, "duration": 2.0}],
                }
            )
        ]

    def test_get_transcript_from_youtube_errors_if_no_transcripts(
        self, svc, youtube_api_client
    ):
        video = youtube_api_client.get_video_info.return_value
        video.caption.find_matching_track.return_value = None

        with pytest.raises(YouTubeDataAPIError):
            svc.get_transcript("VIDEO_ID")

    def test_get_transcript_from_db(
        self, db_session, transcript_factory, svc, youtube_api_client
    ):
        # Add our decoy first to check we aren't picking by row number
        decoy_transcript = transcript_factory(transcript_id="en-us")
        transcript = transcript_factory(
            video_id=decoy_transcript.video_id, transcript_id="en"
        )
        # Flush to generate created dates and move the decoy to have a later
        # created date
        db_session.flush()
        decoy_transcript.created += timedelta(hours=1)

        returned_transcript = svc.get_transcript(transcript.video_id)

        youtube_api_client.get_video_info.assert_not_called()
        assert returned_transcript == transcript.transcript

    @pytest.mark.parametrize(
        "video_id,expected_url",
        [
            ("x8TO-nrUtSI", "https://www.youtube.com/watch?v=x8TO-nrUtSI"),
            # YouTube video IDs don't actually contain any characters that
            # require escaping, but this is not guaranteed for the future.
            # See https://webapps.stackexchange.com/questions/54443/format-for-id-of-youtube-video.
            ("foo bar", "https://www.youtube.com/watch?v=foo+bar"),
            ("foo/bar", "https://www.youtube.com/watch?v=foo%2Fbar"),
        ],
    )
    def test_canonical_video_url(self, video_id, expected_url, svc):
        assert expected_url == svc.canonical_video_url(video_id)

    @pytest.fixture
    def youtube_api_client(self):
        return create_autospec(YouTubeAPIClient, spec_set=True, instance=True)

    @pytest.fixture
    def svc(self, db_session, http_service, youtube_api_client):
        return YouTubeService(
            db_session=db_session,
            enabled=True,
            api_client=youtube_api_client,
            api_key=sentinel.api_key,
            http_service=http_service,
        )


class TestFactory:
    def test_it(
        self,
        pyramid_request,
        http_service,
        db_session,
        YouTubeService,
        YouTubeAPIClient,
    ):
        returned = factory(sentinel.context, pyramid_request)

        YouTubeAPIClient.assert_called_once_with()
        YouTubeService.assert_called_once_with(
            db_session=db_session,
            enabled=pyramid_request.registry.settings["youtube_transcripts"],
            api_client=YouTubeAPIClient.return_value,
            api_key="test_youtube_api_key",
            http_service=http_service,
        )
        assert returned == YouTubeService.return_value

    @pytest.fixture(autouse=True)
    def YouTubeAPIClient(self, patch):
        return patch("via.services.youtube.YouTubeAPIClient")

    @pytest.fixture(autouse=True)
    def YouTubeService(self, patch):
        return patch("via.services.youtube.YouTubeService")
