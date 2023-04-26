# TODO we probably should abstract part of this to GoolgleAPI with the common bits from GoogleDrive
import re
from logging import getLogger

from google.oauth2.service_account import Credentials
from google.auth.transport.requests import AuthorizedSession
from youtube_transcript_api import YouTubeTranscriptApi, Transcript

from via.exceptions import ConfigurationError
from via.services.http import HTTPService
from dataclasses import dataclass

LOG = getLogger(__name__)


@dataclass
class YoutubeTranscript:
    transcript: Transcript
    language: str


class YoutubeAPI:
    def get_transcript(self, video_id):
        transcripts = self._get_transcripts(video_id)

        if len(transcripts) > 1:
            raise ValueError("Need to pick the right one")

        transcript = transcripts[0].transcript.fetch()

        return transcript

    def _get_transcripts(self, video_id):
        # https://github.com/jdepoix/youtube-transcript-api#list-available-transcripts
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)

        return [
            YoutubeTranscript(transcript=transcript, language=transcript.language_code)
            for transcript in transcripts
        ]

    @classmethod
    def parse_file_url(cls, public_url):
        # TODO this needs to accept more formats
        if match := re.match(
            r"^https://www.youtube.com/watch\?v=([\w_&]+)$", public_url
        ):
            return match.group(1)

        return None
