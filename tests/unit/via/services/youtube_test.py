from unittest.mock import patch, sentinel

import pytest
from youtube_transcript_api import Transcript

from via.services.youtube import YoutubeService, factory


def _transcript(language_code, is_generated):
    return Transcript(
        sentinel.http,
        sentinel.video_id,
        sentinel.url,
        language_code,
        language_code,
        is_generated,
        [],
    )


class TestYoutubeService:
    @pytest.mark.parametrize(
        "url,video_id",
        [
            ("not_an_url", None),
            ("https://notyoutube:1000000", None),
            ("https://notyoutube.com", None),
            ("https://youtube.com", None),
            ("https://youtube.com?param=nope", None),
            ("https://youtube.com?v=", None),
            ("https://www.youtube.com/watch?v=VIDEO_ID", "VIDEO_ID"),
            ("https://www.youtube.com/watch?v=VIDEO_ID&t=14s", "VIDEO_ID"),
        ],
    )
    def test_parse_file_url(self, url, video_id):
        assert video_id == YoutubeService.parse_url(url)

    @pytest.mark.parametrize("enabled,expected", [(True, True), (False, False)])
    def test_enabled(self, enabled, expected):
        assert YoutubeService(enabled).enabled == expected

    def test_get_transcript(self, svc, YouTubeTranscriptApi, _pick_transcript):
        transcript = svc.get_transcript(sentinel.video_id)

        YouTubeTranscriptApi.list_transcripts.assert_called_once_with(sentinel.video_id)
        _pick_transcript.assert_called_once_with(
            YouTubeTranscriptApi.list_transcripts.return_value,
            preferred_language_code="en",
        )

        assert transcript == _pick_transcript.return_value.fetch.return_value

    def test_get_transcript_when_none_available(
        self, svc, YouTubeTranscriptApi, _pick_transcript
    ):
        _pick_transcript.return_value = None

        transcript = svc.get_transcript(sentinel.video_id)

        assert not transcript

    @pytest.mark.parametrize(
        "language_code,transcripts,expected_is_generated,expected_language_code",
        [
            (
                "en",
                [_transcript("en", True), _transcript("en", False)],
                True,
                "en",
            ),
            (
                "en",
                [_transcript("fr", True), _transcript("en", False)],
                True,
                "fr",
            ),
            (
                "en",
                [_transcript("en", False), _transcript("fr", False)],
                False,
                "en",
            ),
            (
                "en",
                [_transcript("fr", False), _transcript("de", False)],
                False,
                "fr",
            ),
        ],
    )
    def test__pick_transcript(
        self,
        svc,
        language_code,
        transcripts,
        expected_is_generated,
        expected_language_code,
    ):
        transcript = svc._pick_transcript(  # pylint:disable=protected-access
            transcripts, language_code
        )

        assert transcript.is_generated == expected_is_generated
        assert transcript.language_code == expected_language_code

    @pytest.fixture
    def _pick_transcript(self, svc):
        with patch.object(svc, "_pick_transcript") as _pick_transcript:
            yield _pick_transcript

    @pytest.fixture
    def svc(self):
        return YoutubeService(enabled=True)

    @pytest.fixture
    def YouTubeTranscriptApi(self, patch):
        return patch("via.services.youtube.YouTubeTranscriptApi")


def test_factory(pyramid_request):
    svc = factory(sentinel.context, pyramid_request)

    assert isinstance(svc, YoutubeService)
