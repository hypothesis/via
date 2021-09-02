import re
from glob import glob
from shelve import DbfilenameShelf
from urllib.parse import parse_qs, urlparse

DRIVE_REGEX = (
    re.compile(r"https://drive.google.com/.*uc\?id=(.*)(?:&export=download)"),
    re.compile(r"https://drive.google.com.*/file/d/([^/]*)"),
)


def extract(url):
    for regex in DRIVE_REGEX:
        if match := regex.search(url):
            return match.group(1)

    if "drive.google.com" not in url:
        return None

    parsed = urlparse(url)
    if "/folders/" in parsed.path:
        return None

    if query := parse_qs(parsed.query):
        if file_id := query.get("id"):
            return file_id[0]

    raise ValueError(f"Cannot parse URL: {url}")


def get_raw_ids():
    for source in glob("data/*.csv"):
        with open(source) as handle:
            for row in handle:
                try:
                    file_id = extract(row.strip())
                except ValueError as err:
                    print(err)

                if file_id:
                    yield file_id


if __name__ == "__main__":
    with DbfilenameShelf("data/db/file_id.db") as db:
        total, new = 0, 0

        for file_id in set(get_raw_ids()):
            total += 1
            if file_id not in db:
                new += 1
                db[file_id] = None

    print(f"Found {total} unique file ids of which {new} were new")
