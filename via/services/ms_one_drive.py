import re


class MSOneDriveService:
    URL_REGEXPS = (
        re.compile(r"^https://.*\.sharepoint.com/.*download=1"),
        re.compile(r"^https://api.onedrive.com/v1.0/.*/root/content"),
    )

    @classmethod
    def is_one_drive_url(cls, url):
        return any(regexp.match(url) for regexp in cls.URL_REGEXPS)


def factory(_context, _request):
    return MSOneDriveService()
