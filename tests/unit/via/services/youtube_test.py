from datetime import timedelta
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
        "enabled,api_key,expected",
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
            ).enabled
            == expected
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

    def test_get_transcript(self, db_session, svc, YouTubeTranscriptApi):
        YouTubeTranscriptApi.get_transcript.return_value = [
            {"text": "foo", "start": 0.0, "duration": 1.0},
            {"text": "bar", "start": 1.0, "duration": 2.0},
        ]

        returned_transcript = svc.get_transcript("test_video_id")

        YouTubeTranscriptApi.get_transcript.assert_called_once_with(
            "test_video_id", languages=("en",)
        )
        assert returned_transcript == YouTubeTranscriptApi.get_transcript.return_value
        # It should have cached the transcript in the DB.
        assert db_session.scalars(select(Transcript)).all() == [
            Any.instance_of(Transcript).with_attrs(
                {
                    "video_id": "test_video_id",
                    "transcript": YouTubeTranscriptApi.get_transcript.return_value,
                }
            )
        ]

    def test_get_transcript_returns_cached_transcripts(
        self, db_session, transcript_factory, svc, YouTubeTranscriptApi
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

        YouTubeTranscriptApi.get_transcript.assert_not_called()
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
    def svc(self, db_session, http_service):
        return YouTubeService(
            db_session=db_session,
            enabled=True,
            api_key=sentinel.api_key,
            http_service=http_service,
        )


class TestFactory:
    def test_it(
        self, YouTubeService, youtube_service, pyramid_request, http_service, db_session
    ):
        returned = factory(sentinel.context, pyramid_request)

        YouTubeService.assert_called_once_with(
            db_session=db_session,
            enabled=pyramid_request.registry.settings["youtube_transcripts"],
            api_key="test_youtube_api_key",
            http_service=http_service,
        )
        assert returned == youtube_service

    @pytest.fixture(autouse=True)
    def YouTubeService(self, patch):
        return patch("via.services.youtube.YouTubeService")

    @pytest.fixture
    def youtube_service(self, YouTubeService):
        return YouTubeService.return_value


@pytest.fixture(autouse=True)
def YouTubeTranscriptApi(patch):
    return patch("via.services.youtube.YouTubeTranscriptApi")
