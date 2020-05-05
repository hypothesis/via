"""Methods for reading and writing domains to CSV."""

import csv

from html_test_harness.domain import Domain


class CSVData:
    @staticmethod
    def from_csv(filename, max_rows=None):
        with open(filename) as handle:
            read_rows = False

            for pos, row in enumerate(csv.reader(handle)):
                if max_rows and pos > max_rows:
                    return

                if not read_rows:
                    read_rows = True
                else:
                    domain_name, exclude, _exclude_reason, url, count = row
                    yield Domain(domain_name, url, count, exclude)

    @staticmethod
    def to_csv(filename, domains):
        with open(filename, 'w') as handle:
            writer = csv.writer(handle)

            # Headers
            writer.writerow(
                ['domain', 'exclude', 'exclude_reason', 'url', 'count'])

            for domain in domains:
                writer.writerow([
                    domain.name,
                    '' if domain.is_valid else 1,
                    '' if domain.is_valid else domain.invalid_message,
                    domain.url,
                    domain.count
                ])


