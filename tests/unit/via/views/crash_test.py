from unittest.mock import sentinel

import pytest

from via.views.crash import crash


def test_it():
    with pytest.raises(RuntimeError):
        crash(sentinel.request)
