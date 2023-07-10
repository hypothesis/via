from urllib.parse import parse_qs, quote_plus, urlparse

from youtube_transcript_api import YouTubeTranscriptApi


class YouTubeService:
    def __init__(self, enabled: bool):
        self._enabled = enabled

    @property
    def enabled(self):
        return self._enabled

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

        if parsed.netloc not in ["www.youtube.com", "youtube.com"]:
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

    def get_transcript(self, video_id):
        """
        Call the YouTube API and return the transcript for the given video_id.

        :raise Exception: this method might raise any type of exception that
            YouTubeTranscriptApi raises
        """
        return YouTubeTranscriptApi.get_transcript(video_id)


def factory(_context, request):
    return YouTubeService(enabled=request.registry.settings["youtube_transcripts"])
