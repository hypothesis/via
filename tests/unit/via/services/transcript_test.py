from io import BytesIO
from unittest.mock import create_autospec

import pytest
from requests.models import Response

from via.services.http import HTTPService
from via.services.transcript import TranscriptService, factory


def make_response(status: int, text: str) -> Response:
    rsp = Response()
    rsp.status_code = status
    rsp.raw = BytesIO(text.encode("utf-8"))
    return rsp


EXAMPLE_WEBVTT = """WEBVTT

00:11.000 --> 00:13.000
<v Roger Bingham>We are in New York City

00:13.000 --> 00:16.000
<v Roger Bingham>We're actually at the Lucern Hotel, just down the street
"""

EXAMPLE_SRT = """
1
00:00:11,000 --> 00:00:13,000
We are in New York City

2
00:00:13,000 --> 00:00:16,000
We're actually at the Lucern Hotel, just down the street
"""

EXAMPLE_TRANSCRIPT = [
    {"start": 11.0, "duration": 2.0, "text": "We are in New York City"},
    {
        "start": 13.0,
        "duration": 3.0,
        "text": "We're actually at the Lucern Hotel, just down the street",
    },
]


class TestTranscriptService:
    @pytest.mark.parametrize(
        "url,content,expected",
        [
            ("https://example.com/transcript.vtt", EXAMPLE_WEBVTT, EXAMPLE_TRANSCRIPT),
            ("https://example.com/transcript.srt", EXAMPLE_SRT, EXAMPLE_TRANSCRIPT),
        ],
    )
    def test_get_transcript(self, svc, http_service, url, content, expected):
        http_service.get.return_value = make_response(200, content)
        transcript = svc.get_transcript(url)

        http_service.get.assert_called_with(url)
        assert transcript == expected

    @pytest.fixture
    def svc(self, http_service):
        return TranscriptService(http_service=http_service)

    @pytest.fixture
    def http_service(self):
        return create_autospec(HTTPService, spec_set=True, instance=True)


@pytest.mark.usefixtures("http_service")
def test_factory(pyramid_request):
    factory({}, pyramid_request)
