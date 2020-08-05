from html_test_harness.url_for import URLFor
from html_test_harness.domain import Domain

from html_test_harness.domain_store import DomainStore
from requests import get, RequestException

from via.services.timeit import timeit

domain_store = DomainStore()


def make_urls(url_gen):
    urls_to_request = []

    for domain_name in domain_store.domain_names:
        domain = domain_store.get(domain_name, request=False)
        if not domain.is_valid:
            continue

        urls_to_request.append(url_gen(domain.url))

    return urls_to_request


def get_em(urls_to_request):
    error_url = []
    ttfb = []

    ms_callback = lambda ms: ttfb.append(ms)

    for pos, url in enumerate(urls_to_request):
        if pos % 250 == 0:
            print(pos)

        try:
            resp = get(url)
            resp.raise_for_status()

        except RequestException:
            error_url.append(url)
            print(pos, resp, url)

    return pos, error_url


url_for = URLFor()

for rewriter in ('null', 'null_stream', 'lxml', 'lxml_stream', 'htmlparser'):

    url_gen = lambda url: url_for.proxy_rewriter(url, rewriter)
    #url_gen = lambda url: url_for.nginx_proxy(url)

    urls_to_request = make_urls(url_gen)

    with timeit(rewriter):
        total, error_urls = get_em(urls_to_request)
        print()

    print("TOTAL", total, "errors", len(error_urls))

