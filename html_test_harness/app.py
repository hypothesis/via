from urllib.parse import urlparse, urlencode

from flask import Flask, render_template

from html_test_harness.domain_store import DomainStore
from html_test_harness.domain import Domain

app = Flask(__name__)


def get_domains():
    domain_store = DomainStore()

    domains = []
    domains_by_url = {}
    count = 0

    for domain in domain_store:
        if not domain.is_valid:
            continue

        if count > 100:
            break
        count += 1

        domains.append(domain)
        domains_by_url[domain.url] = domain

    return domains, domains_by_url


DOMAINS, DOMAINS_BY_URL = get_domains()


def url_for(link):
    url = urlparse('http://localhost:9082/html')
    url = url._replace(query=urlencode({'url': link}))

    return url.geturl()


@app.route('/')
def list():
    return render_template('list.html.jinja2', domains=DOMAINS, url_for=url_for)


if __name__ == '__main__':
    app.run(debug=True)