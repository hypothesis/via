from urllib.parse import parse_qs, quote_plus, urlparse

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from youtube_transcript_api import YouTubeTranscriptApi

from via.models import Transcript
from via.services.http import HTTPService


class YouTubeDataAPIError(Exception):
    """A problem with calling the YouTube Data API."""


class YouTubeService:
    def __init__(
        self, db_session, enabled: bool, api_key: str, http_service: HTTPService
    ):
        self._db = db_session
        self._enabled = enabled
        self._api_key = api_key
        self._http_service = http_service

    @property
    def enabled(self):
        return bool(self._enabled and self._api_key)

    def canonical_video_url(self, video_id: str) -> str:
        """
        Return the canonical URL for a YouTube video.

        This is used as the URL which YouTube transcript annotations are
        associated with.
        """
        escaped_id = quote_plus(video_id)
        return f"https://www.youtube.com/watch?v={escaped_id}"

    def get_video_id(self, url):
        """Return the YouTube video ID from the given URL, or None."""
        parsed = urlparse(url)
        path_parts = parsed.path.split("/")

        # youtu.be/VIDEO_ID
        if parsed.netloc == "youtu.be" and len(path_parts) >= 2 and not path_parts[0]:
            return path_parts[1]

        if parsed.netloc not in ["www.youtube.com", "youtube.com", "m.youtube.com"]:
            return None

        query_params = parse_qs(parsed.query)

        # https://youtube.com?v=VIDEO_ID, youtube.com/watch?v=VIDEO_ID, etc.
        if "v" in query_params:
            return query_params["v"][0]

        path_parts = parsed.path.split("/")

        # https://yotube.com/v/VIDEO_ID, /embed/VIDEO_ID, etc.
        if (
            len(path_parts) >= 3
            and not path_parts[0]
            and path_parts[1] in ["v", "embed", "shorts", "live"]
        ):
            return path_parts[2]

        return None

    def get_video_title(self, video_id):
        """Call the YouTube API and return the title for the given video_id."""
        # https://developers.google.com/youtube/v3/docs/videos/list
        try:
            return self._http_service.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={
                    "id": video_id,
                    "key": self._api_key,
                    "part": "snippet",
                    "maxResults": "1",
                },
            ).json()["items"][0]["snippet"]["title"]
        except Exception as exc:
            raise YouTubeDataAPIError("getting the video title failed") from exc

    def get_transcript(self, video_id):
        """
        Call the YouTube API and return the transcript for the given video_id.

        :raise Exception: this method might raise any type of exception that
            YouTubeTranscriptApi raises
        """
        transcript_id = language_code = "en"

        try:
            transcript = (
                self._db.scalars(
                    select(Transcript).where(
                        Transcript.video_id == video_id,
                        Transcript.transcript_id == transcript_id,
                    )
                )
                .one()
                .transcript
            )
        except NoResultFound:
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id, languages=(language_code,)
            )
            self._db.add(
                Transcript(
                    video_id=video_id,
                    transcript_id=transcript_id,
                    transcript=transcript,
                )
            )

        return transcript


def factory(_context, request):
    return YouTubeService(
        db_session=request.db,
        enabled=request.registry.settings["youtube_transcripts"],
        api_key=request.registry.settings["youtube_api_key"],
        http_service=request.find_service(HTTPService),
    )
