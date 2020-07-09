from unittest.mock import sentinel

import pytest

from via.cache_buster import PathCacheBuster


class TestPathCacheBuster:
    EXPECTED_HASH = "606e8d07c0af18c736c272a592038742"

    def test_salt_is_generated_from_dir_hash(self, cache_buster):
        assert cache_buster.salt == self.EXPECTED_HASH

    def test_salt_changes_on_new_file(self, static_dir):
        new_file = static_dir / "new_file.txt"
        new_file.write_text("NEW")

        assert PathCacheBuster(static_dir).salt != self.EXPECTED_HASH

    def test_salt_changes_on_content_change(self, static_dir):
        style_file = static_dir / "style.css"
        style_file.write_text("SOMETHING DIFFERENT")

        assert PathCacheBuster(static_dir).salt != self.EXPECTED_HASH

    def test_immutable_test(self, cache_buster):
        test = cache_buster.get_immutable_file_test()

        assert not test(sentinel.path, "/woo.txt")
        assert test(sentinel.path, cache_buster.immutable_path + "/woo.txt")

    def test_rewriting(self, cache_buster):
        response = cache_buster(sentinel.request, "css/style.css", sentinel.kwargs)

        assert response == (f"{cache_buster.salt}/css/style.css", sentinel.kwargs)

    @pytest.fixture
    def static_dir(self, tmp_path):
        for name, content in (
            ("style.css", "CSS"),
            ("index.html", "HTML"),
        ):
            path = tmp_path / name
            path.write_text(content)

        return tmp_path

    @pytest.fixture
    def cache_buster(self, static_dir):
        return PathCacheBuster(static_dir)
