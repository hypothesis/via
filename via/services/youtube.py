class YouTubeService:
    def __init__(self, enabled: bool):
        self._enabled = enabled

    @property
    def enabled(self):
        return self._enabled


def factory(_context, request):
    return YouTubeService(enabled=request.registry.settings["youtube_transcripts"])
