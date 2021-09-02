import gevent.monkey

gevent.monkey.patch_all()

import json
import random
from collections import deque
from datetime import datetime, timedelta
from shelve import DbfilenameShelf

import gevent

from via.services import GoogleDriveAPI


class ETA:
    def __init__(self, total, progress):
        self.total = total
        self.progress = progress
        self.last_timestamp = None
        self.report_every = 100

    def increment(self):
        self.progress += 1
        if self.progress % self.report_every == 0:
            self.report()

    def report(self):
        print(f"Prog: {self.progress}/{self.total}")
        timestamp = datetime.now()
        remaining = self.total - self.progress

        if self.last_timestamp:
            diff = timestamp - self.last_timestamp
            sec = diff.seconds + diff.microseconds / 1000000
            items = self.report_every

            print(f"\t{sec} seconds for {items} items ({items / sec} item/s)")

            per_item = sec / items
            eta = timedelta(seconds=remaining * per_item)
            print(f"\t{remaining} remaining (ETA: {eta})")
        else:
            print(f"\t{remaining} remaining")

        self.last_timestamp = timestamp


class GoogleDriveUpdater:
    def __init__(self, db):
        with open("data/credentials.json") as handle:
            self.sessions = [
                GoogleDriveAPI(credentials)._session
                for credentials in json.load(handle)
            ]

        self.active_session = 0
        self.db = db

    @property
    def session(self):
        self.active_session += 1
        self.active_session %= len(self.sessions)

        return self.sessions[self.active_session]

    def get_worklist(self, should_refresh):
        file_ids = deque()

        for file_id, data in self.db.items():
            if should_refresh(file_id, data):
                file_ids.append(file_id)

        return file_ids

    def process_worklist(
        self, worklist: deque, eta: ETA, num_workers=None, worker_delay=None
    ):
        if num_workers is None:
            num_workers = 8 * len(self.sessions)
        if worker_delay is None:
            # It seems a bit odd to have a delay on workers and lots of workers
            # but it means that when a worker backs off due to throttling we
            # loose a lower percentage of our total workers. It also means
            # our workers don't go in totally hard one request after another,
            # which seems to balance out to getting blocked less often, and
            # letting us hover right by the line.
            worker_delay = 0.70

        def worker(worker_id):
            print(f"Worker {worker_id} jittering...")
            self.jitter()
            print(f"\tWorker {worker_id} starts")

            while worklist:
                file_id = worklist.pop()

                try:
                    self.db[file_id] = self.get_file_data(file_id)
                    eta.increment()
                except Exception as err:
                    print(f"Failed to get {file_id}: {err}")
                    print("\tWork was re-queued to do again later...")
                    worklist.appendleft(file_id)

                gevent.sleep(worker_delay)

            print(f"Worker {worker_id} ends...")

        threads = []
        for i in range(num_workers):
            threads.append(gevent.spawn(worker, i))

        gevent.joinall(threads)

    def get_file_data(self, file_id):
        fields = "id,name,linkShareMetadata,resourceKey,createdTime,modifiedTime,owners"

        response = self.session.get(
            url=f"https://www.googleapis.com/drive/v3/files/{file_id}?fields={fields}",
            headers={
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate",
                "User-Agent": "(gzip)",
            },
            timeout=5,
        )

        response_json = response.json()

        if response.status_code == 403:
            print(f"THROTTLING! Backing off: {file_id}")
            self.jitter(min_seconds=5, max_seconds=10)

            return self.get_file_data(file_id)

        return {
            "file_id": file_id,
            "status_code": response.status_code,
            "resource_key": "resourceKey" in response_json,
            "data": response_json,
        }

    @staticmethod
    def jitter(min_seconds=0, max_seconds=10):
        jitter = min_seconds + random.random() * (max_seconds - min_seconds)
        # print(f"\tJittering for {jitter}s")
        gevent.sleep(jitter)


class RefreshReasons:
    @staticmethod
    def file_id_is_new(_file_id, data):
        return data is None

    @staticmethod
    def quick_check(file_id, data):
        # This seems to be all of them so far
        if not file_id.startswith("0B"):
            return False

        # Don't bother re-checking 404s, they aren't coming back
        if data and data["status_code"] == 404:
            return False

        return True

    @staticmethod
    def recheck(_file_id, data):
        # Check new things
        if data is None:
            return True

        # Don't bother re-checking 404s, they aren't coming back
        if data["status_code"] == 404:
            return False

        # We will recheck things even if they have a resource key, as they
        # could have been deleted.
        return True


with DbfilenameShelf("data/db/file_id.db") as db:
    updater = GoogleDriveUpdater(db)
    worklist = updater.get_worklist(should_refresh=RefreshReasons.file_id_is_new)

    if not worklist:
        print("No work to do")
        exit()

    eta = ETA(total=len(db), progress=len(db) - len(worklist))
    eta.report()

    updater.process_worklist(worklist, eta)
