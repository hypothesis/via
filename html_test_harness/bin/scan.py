"""
Scans the domains for errors and builds the local cache of content.

This script will request all of the domains and build a local cache allowing
quick access to the responses.

The initial run will be quite slow.
"""

from pkg_resources import resource_filename

from html_test_harness.csv_data import CSVData
from html_test_harness.domain_store import DomainStore
# For picking purposes
from html_test_harness.domain import Domain


if __name__ == '__main__':
    harness = DomainStore()

    total_millis = 0
    total_valid = 0

    for pos, domain in enumerate(harness):
        millis = domain.meta['millis']
        total_millis += millis
        millis = str(millis) + 'ms'

        if domain.is_valid:
            total_valid += 1
            print(pos, "OK", domain, millis)
        else:
            print(pos, domain, millis, '>>>', domain.invalid_message)

    output = resource_filename('html_test_harness', 'data/example_urls.scanned.csv')

    CSVData.to_csv(output, harness)

    print(f"\nWrote: {output}.")
    print(f"Total scan time: {total_millis}ms")
    print(f"Valid URLs: {total_valid}/{pos} ({100 * total_valid / pos})%")