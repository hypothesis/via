"""Pyramid CacheBusters."""

import os


class PathCacheBuster:
    """A cache buster which modifies paths to enable immutable caching.

    Implements `pyramid.interfaces.ICacheBuster` and can be used with
    `config.add_cache_buster()` to enable rewriting of URLs to a version
    which contains the last modified time.

    This allows assets to be statically cached until at least one of them has
    changed. This is achieved by generating a salt value from the last
    modified time of the files which is applied to the input URL.

    :param path: Path to static for generating the salt value
    """

    def __init__(self, path):
        self.salt = self._generate_salt(path)

    def __call__(self, request, subpath, kw):  # pylint: disable=invalid-name
        """Prepend the salt to the path.

        Implements the ICacheBuster iterface.
        """
        return f"{self.salt}/{subpath}", kw

    @property
    def immutable_path(self):
        """Return the external URL where immutable content is accessible."""
        return f"/static/{self.salt}"

    def get_immutable_file_test(self):
        """Return an immutability test for use with Whitenoise."""
        immutable_path = self.immutable_path

        def _test(_, url):
            return url.startswith(immutable_path)

        return _test

    @staticmethod
    def _generate_salt(path):
        """Generate salt based on the last modified time.

        This ensures we only change salt when at least one file has changed.
        """
        max_mtime = 0

        for base_dir, _, file_names in os.walk(path):
            for file_name in file_names:
                path = os.path.join(base_dir, file_name)
                max_mtime = max(max_mtime, os.stat(path).st_mtime)

        return str(max_mtime)
