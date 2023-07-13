from io import BytesIO
from unittest.mock import sentinel

import pytest
from requests import Response

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
    def test_enabled(self, enabled, api_key, expected):
        assert (
            YouTubeService(
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

    def test_get_video_title(self, svc, http_service):
        response = http_service.get.return_value = Response()
        response.raw = BytesIO(b'{"items": [{"snippet": {"title": "video_title"}}]}')

        title = svc.get_video_title(sentinel.video_id)

        http_service.get.assert_called_once_with(
            "https://www.googleapis.com/youtube/v3/videos",
            params={
                "id": sentinel.video_id,
                "key": sentinel.api_key,
                "part": "snippet",
                "maxResults": "1",
            },
        )
        assert title == "video_title"

    def test_get_video_title_raises_YouTubeDataAPIError(self, svc, http_service):
        http_service.get.side_effect = RuntimeError()

        with pytest.raises(YouTubeDataAPIError) as exc_info:
            svc.get_video_title(sentinel.video_id)

        assert exc_info.value.__cause__ == http_service.get.side_effect

    def test_get_transcript(self, YouTubeTranscriptApi, svc):
        transcript = svc.get_transcript(sentinel.video_id)

        YouTubeTranscriptApi.get_transcript.assert_called_once_with(sentinel.video_id)
        assert transcript == YouTubeTranscriptApi.get_transcript.return_value

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
    def svc(self, http_service):
        return YouTubeService(
            enabled=True, api_key=sentinel.api_key, http_service=http_service
        )


class TestFactory:
    def test_it(self, YouTubeService, youtube_service, http_service, pyramid_request):
        returned = factory(sentinel.context, pyramid_request)

        YouTubeService.assert_called_once_with(
            enabled=True, api_key="test_youtube_api_key", http_service=http_service
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
