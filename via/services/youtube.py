from typing import List
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import Transcript, YouTubeTranscriptApi


class YoutubeService:
    def __init__(self, enabled: bool):
        self._enabled = enabled

    @property
    def enabled(self):
        return self._enabled

    @classmethod
    def parse_url(cls, public_url):
        """Get the youtube video ID from an URL."""
        parsed = urlparse(public_url)
        if parsed.netloc not in ["www.youtube.com", "youtube.com"]:
            return None

        if not parsed.query:
            return None

        query_params = parse_qs(parsed.query)
        if "v" not in query_params:
            return None

        return query_params["v"][0]

    def get_transcript(self, video_id, preferred_language_code="en"):
        transcripts = self._get_transcripts(video_id)
        if transcript := self._pick_transcript(
            transcripts, preferred_language_code=preferred_language_code
        ):
            return transcript.fetch()

        return None

    def _pick_transcript(self, transcripts: List[Transcript], preferred_language_code):
        """Pick a transcript out of a list of them.

        For now the logic is:
            - Prefer user transcripts over generated ones
            - Of those prefer the `preferred_language_code` one
            - If none available, pick "the first one"
            - If there are no user transcripts follow the same process on the machine generated ones
        """
        user_transcripts = {t.language_code: t for t in transcripts if t.is_generated}
        generated_transcripts = {
            t.language_code: t for t in transcripts if not t.is_generated
        }

        if user_transcripts:
            return user_transcripts.get(
                preferred_language_code, list(user_transcripts.values())[0]
            )

        return generated_transcripts.get(
            preferred_language_code, list(generated_transcripts.values())[0]
        )

    def _get_transcripts(self, video_id):
        return YouTubeTranscriptApi.list_transcripts(video_id)


def factory(_context, request):
    return YoutubeService(enabled=request.registry.settings["youtube_captions"])
