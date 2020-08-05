from requests import get
from datetime import datetime

from urllib3 import HTTPResponse

from html_test_harness.domain import Domain
from html_test_harness.domain_store import DomainStore
from html_test_harness.url_for import URLFor
from via.services.timeit import timeit


def ms(delta):
    return delta.seconds * 1000 + delta.microseconds / 1000


def ms_since(start):
    return ms(datetime.utcnow() - start)


def ttfb(url):
    start = datetime.utcnow()

    response = get(url, stream=True)

    for chunk in response.iter_content(80):
        break

    time = ms_since(start)

    response.close()

    return time



def stream_profile(url, chunk_size=None, start_after_first_byte=True):
    bytes = 0
    if not start_after_first_byte:
        start = datetime.utcnow()
        yield ms_since(start), 0

    response = get(url, stream=True)

    if start_after_first_byte:
         start = datetime.utcnow()

    yield ms_since(start), 0

    for chunk in response.iter_content(chunk_size=chunk_size):
        bytes += len(chunk)
        yield ms_since(start), bytes

a = HTTPResponse()


def stream_comparison(url, chunk_sizes=(128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, None)):
    for chunk_size in chunk_sizes:
        for _ in range(5):
            start = datetime.utcnow()
            response = get(url, stream=True)

            for chunk in response.iter_content(chunk_size=chunk_size):
                pass

            yield chunk_size, ms_since(start)


from matplotlib import pyplot as plt
from matplotlib.pyplot import figure, gcf
import numpy as np


def compare_rewriters(original_url):
    for rewriter in (
    "htmlparser", "lxml_stream", "lxml", "null_stream", "null"):
        url = URLFor.rewriter(original_url, rewriter=rewriter)
        print(rewriter, url)
        points = list(stream_profile(url, chunk_size=None, start_after_first_byte=False))

        yield rewriter, points


def compare_chunk_size_in(original_url, rewriter):
    for chunk_size_in in (128, 1024, 8192, 16384, 32768, 65536):
        url = URLFor.proxy_rewriter(original_url, rewriter=rewriter, extras={'via.csi': chunk_size_in})
        label = f"{rewriter} csi:{chunk_size_in}"
        print(label, url)
        with timeit(label):
            points = list(stream_profile(url, chunk_size=None))

        yield label, points



def compare_chunk_size_out(original_url, rewriter):
    for chunk_size_out in (1024, 8192, 16384, 32768, 65536):
        url = URLFor.rewriter(original_url, rewriter=rewriter, extras={'via.cso': chunk_size_out})
        label = f"{rewriter} cso:{chunk_size_out}"
        print(label, url)
        with timeit(label):
            points = list(stream_profile(url, chunk_size=None))

        yield label, points


def top_domains(max=100):
    store = DomainStore()

    domains = []
    for count, domain in enumerate(store):
        if count >= max:
            break

        domains.append(domain)

    return domains


def compare_chunk_size_in_multi(rewriter):
    domains = top_domains(100)

    for chunk_size_in in (8192, 16384, 32768, 65536):
        label = f"{rewriter} csi:{chunk_size_in}"
        points = []

        for domain in domains:
            url = URLFor.proxy_rewriter(domain.url, rewriter=rewriter, extras={'via.csi': chunk_size_in})

            print(label, url)

            start = datetime.utcnow()
            try:
                response = get(url)
            except Exception:
                continue
            time = ms_since(start)

            points.append((time, len(response.content)))

        print(points)

        yield label, points


def compare_ssl_ttfb():
    domains = top_domains(100)
    for rewriter in (
            "lxml_stream",
            #"lxml", "htmlparser", "null_stream", "null"
    ):
        for no_ssl in ('on', ''):
            label = f"{rewriter} no_ssl:{no_ssl}"
            points = []

            for domain in domains:
                url = URLFor.rewriter(domain.url, rewriter=rewriter, extras={'via.no_ssl': no_ssl})

                try:
                    time = ttfb(url)
                except Exception:
                    continue

                print(label, time, url)

                points.append([len(domain.response.content), time])

            print(points)

            yield label, points


def compare_ttfb():
    for rewriter in (
            "lxml", "htmlparser", "lxml_stream", "null_stream", "null"):

        label = rewriter
        points = []
        domains = top_domains(100)

        for domain in domains:
            url = URLFor.rewriter(domain.url, rewriter=rewriter)

            try:
                time = ttfb(url)
            except Exception as e:
                print(e)
                break

            print(label, time, url)

            points.append([len(domain.response.content), time])

        points = list(sorted(points, key=lambda v: v[0]))

        yield label, points


def compare_ttlb():
    for rewriter in (
            "lxml", "htmlparser", "lxml_stream", "null_stream", "null"):

        label = rewriter
        points = []
        domains = top_domains(100)

        for doc_id, domain in enumerate(domains):
            url = URLFor.proxy_rewriter(domain.url, rewriter=rewriter)

            start = datetime.utcnow()
            try:
                get(url)
            except Exception as e:
                print(e)
                break

            time = ms_since(start)

            print(label, time, url)

            points.append([doc_id, time])

        #points = list(sorted(points, key=lambda v: v[0]))

        yield label, points


def multigraph(title, lines, method=plt.plot, axes=None):
    fig = gcf()
    fig.set_size_inches(10, 7)
    #plt.ylim(0, 1000)

    for label, points in lines:
        time, bytes = zip(*points)
        np_time = np.array(time)
        np_bytes = np.array(bytes)

        method(np_time, np_bytes, label=label, marker='+')

    if axes:
        plt.xlabel(axes[0])
        plt.ylabel(axes[1])
    else:
        plt.ylabel("Bytes")
        plt.xlabel("Time")
    plt.title(title[:60])
    plt.legend()
    plt.figure(figsize=(20, 20))


    plt.show()


#original_url = "https://html.spec.whatwg.org/"
#original_url = "http://example.com"
#original_url = "https://www.theguardian.com"
original_url = "https://en.wikipedia.org/wiki/311_(band)"
#original_url = "https://www.wired.com/2014/08/edward-snowden/"
#original_url = "https://www.vice.com/en_us/article/5dmpbz/how-elf-on-the-shelf-became-a-surveillance-state-apparatus"
#original_url = "https://www.nytimes.com/"

import json
multigraph(original_url, compare_rewriters(original_url))

exit()
#multigraph(original_url, compare_chunk_size_in(original_url, "lxml_stream"))
#multigraph(original_url, compare_chunk_size_out(original_url, "lxml_stream"))
#multigraph("Multi", compare_chunk_size_in_multi("htmlparser"), method=plt.scatter)

# results = list(compare_ssl_ttfb())
#

#title = "Chunk size in"

# results = list(compare_ttlb())
title = "Time to last byte"


#results = list(compare_chunk_size_in_multi("lxml_stream"))
# print(results)
#
# with open('_results/run.json', 'w') as fh:
#     json.dump(results, fh)


with open('_results/run.json') as fh:
    results = json.load(fh)


def process(results):
    final = []

    for label, data in results:
        if label == 'lxml_stream':
            order_by = data
            break

    order_by = [v[0] for v in sorted(order_by, key=lambda v: v[1])]

    print(order_by)

    for label, data in results:
        # if label not in ['lxml_stream', 'htmlparser']:
        #     continue

        data = [[order_by.index(d[0]), d[1]] for d in data]
        data = list(sorted(data))

        final.append([label, data[:100]])

    return final

results = process(results)


multigraph(title, results,  axes=['docs', 'ttlb (ms)'])