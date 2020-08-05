class ImageSourceSet:
    def __init__(self, raw):
        self.raw = raw
        self._parts = list(self._parse(raw))

    def map(self, url_function):
        self._parts = [(url_function(url) or url, size) for url, size in self._parts]
        return self

    def __str__(self):
        return ", ".join(f"{url} {size}" for url, size in self._parts)

    @classmethod
    def _parse(self, raw):
        for part in raw.split(","):
            print(part)
            try:
                url, size = part.strip().split(" ", 1)
            except ValueError:
                url, size = part, ""
            yield url, size
