import os

import pytest
from mock import sentinel

from via.cache_buster import PathCacheBuster


class TestPathCacheBuster:
    NEWER = 1500000000
    OLDER = 1400000000

    def test_salt_is_generated_from_newest_mtime(self, cache_buster):
        assert int(float(cache_buster.salt)) == self.NEWER

    def test_immutable_test(self, cache_buster):
        test = cache_buster.get_immutable_file_test()

        assert not test(sentinel.path, "/woo.txt")
        assert test(sentinel.path, cache_buster.immutable_path + "/woo.txt")

    def test_rewriting(self, cache_buster):
        response = cache_buster(sentinel.request, "css/style.css", sentinel.kwargs)

        assert response == (f"{cache_buster.salt}/css/style.css", sentinel.kwargs)

    @pytest.fixture
    def cache_buster(self, tmp_path):
        for name, age, content in (
            ("style.css", self.NEWER, "CSS"),
            ("index.html", self.OLDER, "HTML"),
        ):
            path = tmp_path / name
            path.write_text(content)

            os.utime(str(path), (age, age))

        return PathCacheBuster(tmp_path)
