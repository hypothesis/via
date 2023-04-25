# TODO we probably should abstract part of this to GoolgleAPI with the common bits from GoogleDrive
from logging import getLogger

from google.oauth2.service_account import Credentials
from google.auth.transport.requests import AuthorizedSession
from via.exceptions import ConfigurationError
from via.services.http import HTTPService
from dataclasses import dataclass

LOG = getLogger(__name__)


@dataclass
class YoutubeTranscript:
    id: str
    language: str


class YoutubeAPI:
    # ENABLED here for this demo:

    # https://console.cloud.google.com/apis/library/youtube.googleapis.com?project=via-dev-273714
    SCOPES = [
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ]

    # Configure all the various types of timeout available to us, with the hope
    # that the shortest one will kick in first
    TIMEOUT = 30

    def __init__(self, credentials_list):
        """Initialise the service.

        :param credentials_list: A list of dicts of credentials info as
            provided by Google console's JSON format.
        :raises ConfigurationError: If the credentials are not accepted by Google
        """
        if credentials_list[0].get("disable"):
            LOG.error("Google Drive credentials have been disabled")
            return

        try:
            credentials = Credentials.from_service_account_info(
                credentials_list[0], scopes=self.SCOPES
            )
        except ValueError as exc:
            raise ConfigurationError(
                "The Google Drive service account information is invalid"
            ) from exc

        self._http_service = HTTPService(
            session=AuthorizedSession(credentials, refresh_timeout=self.TIMEOUT),
        )

    def get_transcript(self, video_id):
        transcripts = self._get_transcripts(video_id)

        if len(transcripts) > 1:
            raise ValueError("Need to pick the right one")

        transcript = transcripts[0]

        # TODO researfh if the right way to track languages is while downloading the caption instead of listing them:

        # From: https://developers.google.com/youtube/v3/docs/captions/download

        # The tfmt and tlang parameters are both optional and allow you to download a particular format or machine translation of the track, respectively.
        # The tlang parameter specifies that the API response should return a translation of the specified caption track.

        # Subitle formats:
        # TTML https://en.wikipedia.org/wiki/Timed_Text_Markup_Language
        # WEBVTT https://en.wikipedia.org/wiki/WebVTT
        # sbv – SubViewer subtitle
        # scc – Scenarist Closed Caption format
        # srt – SubRip subtitle

        # https://developers.google.com/youtube/v3/docs/captions/download
        api_url = f"https://www.googleapis.com/youtube/v3/captions/{transcript.id}"

        # THIS APPROACH IS BROKEN, CAN'T RELIAIBLY DOWNLOAD captions
        # https://stackoverflow.com/questions/30653865/downloading-captions-always-returns-a-403
        response = self._http_service.get(api_url, params={"tfmt": "vtt"})

        sub_text = response.text
        print(sub_text)
        return []

    def _get_transcripts(self, video_id):
        # https://www.googleapis.com/youtube/v3/captions
        api_url = "https://www.googleapis.com/youtube/v3/captions"

        response = self._http_service.get(
            api_url, params={"part": ["id", "snippet"], "videoId": video_id}
        )

        """
        {'kind': 'youtube#captionListResponse', 'etag': '36JVF4kLhBidkG8iYfEcWmJnrP8', 'items': [{'kind': 'youtube#caption', 'etag': 'F80xg2LyB-OGUyBIUBoMVTKIjl4', 'id': 'AUieDaa-yuLx4uxXrYEoMr-WSsSlh07t8NiuAj9V1ExFqsKH_qg', 'snippet': {'videoId': 'WQn_W8drKmk', 'lastUpdated': '2023-03-21T20:13:27.316777Z', 'trackKind': 'asr', 'language': 'es', 'name': '', 'audioTrackType': 'unknown', 'isCC': False, 'isLarge': False, 'isEasyReader': False, 'isDraft': False, 'isAutoSynced': False, 'status': 'serving'}}]}

        """

        # TODO include lastUpdated, nice for caching
        # maybe filter out some based "isDraft" and other parameters

        return [
            YoutubeTranscript(id=yt["id"], language=yt["snippet"]["language"])
            for yt in response.json()["items"]
        ]

    @classmethod
    def parse_file_url(cls, public_url):
        # Actually parse the URLs
        return public_url.startswith("https://youtube.com")
