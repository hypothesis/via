"""Copy tox environment variables from devdata."""

import os
from shutil import copy2, rmtree
from subprocess import check_call
from tempfile import mkdtemp


def _get_devdata():
    temp_dir = mkdtemp()
    target = os.path.abspath(".devdata.env")

    try:
        check_call(["git", "clone", "git@github.com:hypothesis/devdata.git", temp_dir])
        copy2(os.path.join(temp_dir, "via/devdata.env"), target)

        print(f"Created {target}")

    finally:
        if os.path.isdir(temp_dir):
            rmtree(temp_dir)


if __name__ == "__main__":
    _get_devdata()
