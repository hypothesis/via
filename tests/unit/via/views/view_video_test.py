from unittest.mock import create_autospec

import pytest

from via.resources import QueryURLResource
from via.views.view_video import video, youtube


class TestYouTube:
    def test_it_returns_restricted_page_when_not_lms(
        self, pyramid_request, secure_link_service
    ):
        secure_link_service.request_has_valid_token.return_value = False
        pyramid_request.params["url"] = "https://youtube.com/watch?v=abc"

        result = youtube(pyramid_request, url="https://youtube.com/watch?v=abc")

        assert result == {"target_url": "https://youtube.com/watch?v=abc"}
        assert pyramid_request.override_renderer == "via:templates/restricted.html.jinja2"

    def test_it_serves_video_when_lms(
        self, pyramid_request, secure_link_service, youtube_service
    ):
        secure_link_service.request_has_valid_token.return_value = True
        pyramid_request.params["url"] = "https://youtube.com/watch?v=abc123"
        youtube_service.get_video_id.return_value = "abc123"
        youtube_service.canonical_video_url.return_value = "https://youtube.com/watch?v=abc123"
        youtube_service.get_video_title.return_value = "Test Video"

        result = youtube(pyramid_request, url="https://youtube.com/watch?v=abc123")

        assert result["player"] == "youtube"
        assert result["video_id"] == "abc123"


class TestVideo:
    def test_it_returns_restricted_page_when_not_lms(
        self, pyramid_request, secure_link_service
    ):
        secure_link_service.request_has_valid_token.return_value = False
        pyramid_request.params["url"] = "https://example.com/video.mp4"
        pyramid_request.params["transcript"] = "https://example.com/transcript.vtt"

        result = video(
            pyramid_request,
            url="https://example.com/video.mp4",
            transcript="https://example.com/transcript.vtt",
        )

        assert result == {"target_url": "https://example.com/video.mp4"}
        assert pyramid_request.override_renderer == "via:templates/restricted.html.jinja2"

    def test_it_serves_video_when_lms(self, pyramid_request, secure_link_service):
        secure_link_service.request_has_valid_token.return_value = True
        pyramid_request.params["url"] = "https://example.com/video.mp4"
        pyramid_request.params["transcript"] = "https://example.com/transcript.vtt"

        result = video(
            pyramid_request,
            url="https://example.com/video.mp4",
            transcript="https://example.com/transcript.vtt",
        )

        assert result["player"] == "html-video"
        assert result["video_url"] == "https://example.com/video.mp4"
