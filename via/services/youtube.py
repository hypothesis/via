from urllib.parse import parse_qs, urlparse


class YoutubeService:
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


def factory(_context, _request):
    return YoutubeService()
