from contextlib import contextmanager
from datetime import datetime


@contextmanager
def timeit(message, ms_callback=None):
    start = datetime.utcnow()
    yield
    diff = datetime.utcnow() - start
    diff = diff.seconds * 1000 + diff.microseconds / 1000

    if ms_callback:
        ms_callback(diff)

    print(f"{diff}ms {message}")
