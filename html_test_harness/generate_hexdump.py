"""
Write out example URL content to _hexdump to serve it from NGINX.

This is to allow us to test without speed being a concern, or hammering
external sites.
"""

# For pickle
from html_test_harness.domain import Domain
from html_test_harness.domain_store import DomainStore

import hashlib


for domain in DomainStore():
    if not domain.is_valid:
        continue

    print(domain.url)
    hash = hashlib.md5()
    hash.update(domain.url.encode('utf-8'))
    filename = hash.hexdigest() + '.html'

    with open("_hexdump/" + filename, 'wb') as handle:
        handle.write(domain.response.content)
