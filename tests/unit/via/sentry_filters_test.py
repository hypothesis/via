from unittest import mock

import pytest

from via.sentry_filters import sentry_before_send_log


class TestSentryBeforeSendLog:
    @pytest.mark.parametrize(
        ("log", "should_be_filtered_out"),
        [
            ({"attributes": {"logger.name": "gunicorn.access"}}, True),
            ({"attributes": {"logger.name": "foo"}}, False),
            ({}, False),
        ],
    )
    def test_it(self, log, should_be_filtered_out):
        result = sentry_before_send_log(log, mock.sentinel.hint)

        if should_be_filtered_out:
            assert result is None
        else:
            assert result == log
