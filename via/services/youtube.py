from dataclasses import asdict
from urllib.parse import parse_qs, quote_plus, urlparse

from h_matchers import Any
from sqlalchemy import select

from via.models import Transcript, Video
from via.services.http import HTTPService
from via.services.youtube_api import CaptionTrack, YouTubeAPIClient


class YouTubeDataAPIError(Exception):
    """A problem with calling the YouTube Data API."""


CAPTION_TRACK_PREFERENCES = (
    # Plain English first
    CaptionTrack(language_code="en"),
    # Plain varieties of English
    CaptionTrack(language_code=Any.string.matching("^en-.*")),
    # Sub-categories of plain English
    CaptionTrack(language_code="en", name=Any()),
    # English varieties with names
    CaptionTrack(language_code=Any.string.matching("^en-.*"), name=Any()),
    # Auto generated English
    CaptionTrack(language_code=Any.string.matching("en"), name=Any(), kind=Any()),
    # Any auto generated English
    CaptionTrack(language_code=Any.string.matching("^en-.*"), name=Any(), kind=Any()),
)


class YouTubeService:
    def __init__(  # pylint: disable=too-many-arguments
        self,
        db_session,
        enabled: bool,
        api_client: YouTubeAPIClient,
        api_key: str,
        http_service: HTTPService,
    ):
        self._db = db_session
        self._enabled = enabled
        self._api_client = api_client
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
        if video := self._db.scalar(select(Video).where(Video.video_id == video_id)):
            return video.title

        try:
            # https://developers.google.com/youtube/v3/docs/videos/list
            title = self._http_service.get(
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

        self._db.add(Video(video_id=video_id, title=title))

        return title

    def get_transcript(self, video_id):
        """
        Call the YouTube API and return the transcript for the given video_id.

        :raise Exception: this method might raise any type of exception that
            YouTubeTranscriptApi raises
        """

        # Find the first transcript we can for this video. We don't mind which
        # one it is
        if transcript_model := self._db.scalars(
            select(Transcript).where(Transcript.video_id == video_id)
            # Sort by transcript create date to increase the chance we return
            # the same transcript should we ever get more than one.
            .order_by(Transcript.created.asc())
        ).first():
            return transcript_model.transcript

        # Then look up a transcript matching our preferences
        video = self._api_client.get_video_info(video_id=video_id)
        caption_track = video.caption.find_matching_track(CAPTION_TRACK_PREFERENCES)
        if not caption_track:
            raise YouTubeDataAPIError(f"No transcript found for '{video_id}'")

        transcript = asdict(self._api_client.get_transcript(caption_track))["text"]
        self._db.add(
            Transcript(
                video_id=video_id, transcript_id=caption_track.id, transcript=transcript
            )
        )
        return transcript


def factory(_context, request):
    return YouTubeService(
        db_session=request.db,
        enabled=request.registry.settings["youtube_transcripts"],
        api_client=YouTubeAPIClient(),
        api_key=request.registry.settings["youtube_api_key"],
        http_service=request.find_service(HTTPService),
    )
