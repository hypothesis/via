from unittest.mock import create_autospec

import pytest
from requests import Response

from via.requests_tools.streaming import stream_bytes


class TestStreamBytes:
    @pytest.mark.parametrize(
        "input_bytes,output",
        (
            ([b"longer_than_chunk_size"], [b"longer_than_chunk_size"]),
            ([b"chunksize"], [b"chunksize"]),
            ([b"chunk", b"size"], [b"chunksize"]),
            ([b"too", b"smol"], [b"toosmol"]),
        ),
    )
    def test_it(self, response, input_bytes, output):
        response.iter_content.return_value = input_bytes

        results = stream_bytes(response, min_chunk_size=9)

        assert list(results) == output
        response.iter_content.assert_called_once_with(chunk_size=9)

    @pytest.fixture
    def response(self):
        return create_autospec(Response, instance=True, spec_set=True)
