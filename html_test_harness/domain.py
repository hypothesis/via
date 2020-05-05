from datetime import datetime

import requests
from requests import RequestException


class Domain:
    """A domain with example url and contents (if requested)."""

    REQUEST_TIMEOUT = 20.0

    def __init__(self, name, url, count, exclude):
        self.name = name
        self.url = url
        self.count = int(count)
        self.exclude = bool(exclude)

        self._meta = None
        self._response = None
        self._error = None

    @property
    def meta(self):
        self.request()
        return self._meta

    @property
    def response(self):
        self.request()
        return self._response

    @property
    def error(self):
        self.request()
        return self._error

    @property
    def requested(self):
        return bool(self._meta)

    @property
    def is_error(self):
        return bool(self.error)

    @property
    def status_code(self):
        return None if self.response is None else self.response.status_code

    @property
    def content_type(self):
        return None if self.response is None else self.response.headers.get('Content-Type')

    def unrequest(self):
        self._meta = None
        self._response = None
        self._error = None

    def request(self):
        if self.requested:
            return

        start = datetime.utcnow()

        try:
            self._response = requests.get(self.url, timeout=self.REQUEST_TIMEOUT)
        except RequestException as err:
            self._error = err

        diff = datetime.utcnow() - start

        self._meta = {
            'millis': diff.microseconds / 1000 + diff.seconds * 1000
        }

    @property
    def is_valid(self):
        return not self.invalid_message

    @property
    def invalid_message(self):
        if self.requested:
            if self.is_error:
                return f'Request error {self.error}'

            if self.status_code != 200:
                return f"Bad status {self.status_code}"

            if 'text/html' not in self.content_type:
                return f"Bad content type {self.content_type}"

        if self.exclude:
            return 'Excluded'

        return None

    def __str__(self):
        additional = ''

        if self.exclude:
            additional += ' EXCLUDED'

        if self.requested:
            if self.is_error:
                additional += f' ERROR:{self.error}'
            else:
                additional += f' {self.status_code}: {self.content_type}'

        return f"<Domain '{self.name}'{additional}>"