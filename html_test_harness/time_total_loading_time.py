from csv import writer
from selenium import webdriver

from html_test_harness.domain import Domain
from html_test_harness.domain_store import DomainStore

domain_store = DomainStore()


def time_url(driver, url):
    driver.get(url)

    # Use the browser Navigation Timing API to get some numbers:
    # https://developer.mozilla.org/en-US/docs/Web/API/Navigation_timing_API
    navigation_start = driver.execute_script(
        "return window.performance.timing.navigationStart")
    doc_interactive = driver.execute_script(
        "return window.performance.timing.domInteractive")
    dom_complete = driver.execute_script(
        "return window.performance.timing.domComplete")

    interactive_time = doc_interactive - navigation_start
    total_time = dom_complete - navigation_start

    return [url, interactive_time, total_time]


def time_it(url_mapper):
    driver = webdriver.Chrome()

    count = 0
    for domain in domain_store:
        if not domain.is_valid:
            continue

        count += 1
        if count >= 100:
            break

        print(domain)
        try:
            results = time_url(driver, url_mapper(domain.url))
        except Exception as e:
            results = [domain.url, 'FAIL', 'FAIL', str(e)]

        print(count, results)
        yield results

    driver.close()


def baseline(url):
    return url


def pywb(url):
    return f"http://localhost:9084/v/{url}"


with open('results/pywb.csv', 'w') as fh:
    csv_file = writer(fh)

    for results in time_it(pywb):
        csv_file.writerow(results)