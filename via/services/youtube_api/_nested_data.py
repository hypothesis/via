from typing import Iterable


def safe_get(data, path: Iterable, default=None):
    """Get deeply nested items without exploding."""

    for key in path:
        try:
            data = data[key]
        except (KeyError, IndexError, TypeError):
            return default

    return data
