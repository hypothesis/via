from pkg_resources import resource_filename

from diskcache import Index

from html_test_harness.csv_data import CSVData


class DomainStore:
    """A collection of domains backed by a disk cache."""

    def __init__(self):
        self.cache_dir = resource_filename(__name__, '_cache')
        self.cache = Index(self.cache_dir)
        self.domain_names = []

        self._prepopulate()

    def unrequest(self, domain_name):
        if domain_name not in self.cache:
            return

        domain = self.cache[domain_name]
        domain.unrequest()
        self.cache[domain] = domain

    def get(self, domain_name, request=False):
        domain = self.cache[domain_name]

        if not request:
            return domain

        if not domain.requested:
            domain.request()

            self.cache[domain_name] = domain

        return domain

    def __iter__(self):
        for domain_name in self.domain_names:
            yield self.get(domain_name, request=True)

    def _prepopulate(self):
        print("Prepopulating...")
        csv_file = resource_filename('html_test_harness', 'data/example_urls.csv')

        for domain in CSVData.from_csv(csv_file):
            self.domain_names.append(domain.name)
            if domain.name in self.cache:
                continue

            self.cache[domain.name] = domain
        print("Done")

