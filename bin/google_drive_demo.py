"""A script to demonstrate different ways of calling Google Drive.

There's no parameters, but you can comment bits in and out to:

* Demonstrate round robin calling with three different credentials sets
* Demonstrate re-using the same credential over and over
* A comparison with getting it the old way
"""

import json
from contextlib import contextmanager
from datetime import datetime
from io import BytesIO
from multiprocessing import Pool

import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

FILE_ID = "1RMhWqrquganFpkmj4f9Nl107HsMp85U1"


class GoogleDriveAPI:
    SCOPES = [
        # If we want metadata
        "https://www.googleapis.com/auth/drive.metadata.readonly",
        # To actually get the file
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    def __init__(self, service_account_info):
        self._credentials = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=self.SCOPES
        )
        self._service = build("drive", "v3", credentials=self._credentials)

    def download_file(self, file_id):
        # https://developers.google.com/drive/api/v3/manage-downloads#download_a_file_stored_on_google_drive
        request = self._service.files().get_media(fileId=file_id)

        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            # print("Download %d%%." % int(status.progress() * 100))

        return fh.getvalue()


@contextmanager
def timeit():
    start = datetime.utcnow()

    yield

    diff = datetime.utcnow() - start
    millis = diff.seconds * 1000 + (diff.microseconds / 1000)
    print(f"{millis}ms")


def worker(args):
    worker_id, credentials = args
    with timeit():
        drive_api = GoogleDriveAPI(credentials)

    for i in range(10):
        with timeit():
            drive_api.download_file(FILE_ID)
            print(f"WORKER {worker_id} {i}")

    print(f"WORKER {worker_id} done")


if __name__ == "__main__":
    # You'll need this file for this to work, but the contents are sensitive
    # so they aren't in git
    with open("google_drive_demo.json") as handle:
        cred_list = json.load(handle)

    pool = Pool(4)

    # Differential credentials for each worker
    pool.map(worker, enumerate(cred_list))

    # The same credentials for each worker
    # pool.map(worker, enumerate(cred_list[0] for _ in cred_list))

    pool.join()

    print("POOL DONE")
    exit()

    # Compare with the speed of getting a single item the old way
    url = f"https://www.googleapis.com/drive/v3/files/{FILE_ID}?key=AIzaSyBULcgo8okrMZfg25nj-zl8as-FH02hI74&alt=media"
    with timeit():
        result = requests.get(url)
        print(result)
        print(result.content)
