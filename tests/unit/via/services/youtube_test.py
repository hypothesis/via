from datetime import datetime
from io import BytesIO
from unittest.mock import sentinel

import pytest
from h_matchers import Any
from requests import Response
from sqlalchemy import select

from via.models import Transcript, Video
from via.services.youtube import YouTubeDataAPIError, YouTubeService, factory


class TestYouTubeService:
    @pytest.mark.parametrize(
        "enabled,api_key,expected",  # noqa: PT006
        [
            (False, None, False),
            (True, None, False),
            (False, sentinel.api_key, False),
            (True, sentinel.api_key, True),
        ],
    )
    def test_enabled(self, db_session, enabled, api_key, expected):
        assert (
            YouTubeService(
                db_session=db_session,
                enabled=enabled,
                api_key=api_key,
                http_service=sentinel.http_service,
                youtube_transcript_service=sentinel.youtube_transcript_service,
            ).enabled
            == expected
        )

    @pytest.mark.parametrize(
        "url,expected_video_id",  # noqa: PT006
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

    def test_get_transcript(
        self, db_session, svc, youtube_transcript_service, transcript_info
    ):
        youtube_transcript_service.pick_default_transcript.return_value = (
            transcript_info
        )
        youtube_transcript_service.get_transcript.return_value = "test_transcript"

        returned_transcript = svc.get_transcript("test_video_id")

        youtube_transcript_service.get_transcript_infos.assert_called_once_with(
            "test_video_id"
        )
        youtube_transcript_service.pick_default_transcript.assert_called_once_with(
            youtube_transcript_service.get_transcript_infos.return_value
        )
        youtube_transcript_service.get_transcript.assert_called_once_with(
            transcript_info
        )
        assert returned_transcript == "test_transcript"
        # It should have cached the transcript in the DB.
        assert db_session.scalars(select(Transcript)).all() == [
            Any.instance_of(Transcript).with_attrs(
                {
                    "video_id": "test_video_id",
                    "transcript_id": transcript_info.id,
                    "transcript": "test_transcript",
                }
            )
        ]

    def test_get_transcript_returns_cached_transcripts(
        self, svc, transcript, youtube_transcript_service
    ):
        returned_transcript = svc.get_transcript(transcript.video_id)

        youtube_transcript_service.get_transcript.assert_not_called()
        assert returned_transcript == transcript.transcript

    def test_get_transcript_retries_when_cached_transcript_is_empty(
        self,
        svc,
        db_session,
        transcript_factory,
        youtube_transcript_service,
        transcript_info,
    ):
        """If the cached transcript has empty segments, delete it and retry from the API."""
        transcript_factory.create(video_id="test_video_id", transcript=[])
        youtube_transcript_service.pick_default_transcript.return_value = (
            transcript_info
        )
        youtube_transcript_service.get_transcript.return_value = "fresh_transcript"

        returned_transcript = svc.get_transcript("test_video_id")

        # It should have called the API to get a fresh transcript.
        youtube_transcript_service.get_transcript_infos.assert_called_once_with(
            "test_video_id"
        )
        assert returned_transcript == "fresh_transcript"
        # The empty cached transcript should have been deleted and replaced.
        transcripts = db_session.scalars(select(Transcript)).all()
        assert len(transcripts) == 1
        assert transcripts[0].transcript == "fresh_transcript"

    def test_get_transcript_does_not_cache_empty_transcript(
        self, svc, db_session, youtube_transcript_service, transcript_info
    ):
        """If the API returns an empty transcript, don't cache it."""
        youtube_transcript_service.pick_default_transcript.return_value = (
            transcript_info
        )
        youtube_transcript_service.get_transcript.return_value = []

        returned_transcript = svc.get_transcript("test_video_id")

        assert returned_transcript == []
        # Nothing should have been cached in the DB.
        assert db_session.scalars(select(Transcript)).all() == []

    def test_get_transcript_returns_oldest_cached_transcript(
        self, transcript_factory, svc
    ):
        """If there are multiple cached transcripts get_transcript() returns the oldest one."""
        oldest_transcript, newer_transcript = transcript_factory.create_batch(
            2, video_id="video_id"
        )
        oldest_transcript.created = datetime(2023, 8, 11)  # noqa: DTZ001
        newer_transcript.created = datetime(2023, 8, 12)  # noqa: DTZ001

        returned_transcript = svc.get_transcript("video_id")

        assert returned_transcript == oldest_transcript.transcript

    @pytest.mark.parametrize(
        "video_id,expected_url",  # noqa: PT006
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
    def svc(self, db_session, http_service, youtube_transcript_service):
        return YouTubeService(
            db_session=db_session,
            enabled=True,
            api_key=sentinel.api_key,
            http_service=http_service,
            youtube_transcript_service=youtube_transcript_service,
        )


class TestFactory:
    def test_it(
        self,
        YouTubeService,
        youtube_service,
        pyramid_request,
        http_service,
        db_session,
        youtube_transcript_service,
    ):
        returned = factory(sentinel.context, pyramid_request)

        YouTubeService.assert_called_once_with(
            db_session=db_session,
            enabled=pyramid_request.registry.settings["youtube_transcripts"],
            api_key="test_youtube_api_key",
            http_service=http_service,
            youtube_transcript_service=youtube_transcript_service,
        )
        assert returned == youtube_service

    @pytest.fixture(autouse=True)
    def YouTubeService(self, patch):
        return patch("via.services.youtube.YouTubeService")

    @pytest.fixture
    def youtube_service(self, YouTubeService):
        return YouTubeService.return_value
