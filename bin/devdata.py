"""Download dev data from github.com:hypothesis/devdata.git."""

import os
from pathlib import Path
from shutil import copyfile
from subprocess import check_call
from tempfile import TemporaryDirectory


def _get_devdata():
    # The directory that we'll clone the devdata git repo into.
    with TemporaryDirectory() as tmp_dir_name:
        git_dir = os.path.join(tmp_dir_name, "devdata")

        check_call(["git", "clone", "git@github.com:hypothesis/devdata.git", git_dir])

        # Copy devdata files into place.
        for source, target in (
            ("via/devdata.env", ".devdata.env"),
            (
                "via/devdata/google_drive_credentials.json",
                ".devdata/google_drive_credentials.json",
            ),
            (
                "via/devdata/google_drive_resource_keys.json",
                ".devdata/google_drive_resource_keys.json",
            ),
        ):
            print(f"Creating {target}...")
            copyfile(
                os.path.join(git_dir, source),
                os.path.join(Path(__file__).parent.parent, target),
            )


if __name__ == "__main__":
    _get_devdata()
