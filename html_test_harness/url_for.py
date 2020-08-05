import hashlib
from urllib.parse import urlparse, urlencode


class URLFor:
    @classmethod
    def proxy_rewriter(cls, link, rewriter, extras=None):
        return cls.rewriter(cls.nginx_proxy(link), rewriter, extras)

    @classmethod
    def nginx_proxy(cls, link):
        hash = hashlib.md5()
        hash.update(link.encode('utf-8'))

        return f'http://localhost:9083/hexdump/{hash.hexdigest()}.html'

    @classmethod
    def test_harness_proxy(cls, link, host='127.0.0.1'):
        url = urlparse(f'http://{host}:5000/proxy')
        url = url._replace(
            query=urlencode({'url': link}))

        return url.geturl()

    @classmethod
    def rewriter(cls, link, rewriter, extras=None):
        url = urlparse('http://localhost:9083/html')
        query = {'url': link, 'via.rewriter': rewriter}
        if extras:
            query.update(extras)

        url = url._replace(query=urlencode(query))

        return url.geturl()

    @classmethod
    def rewriter_with_path(cls, link, rewriter, extras=None):
        url = urlparse('http://localhost:9083')
        doc_url = urlparse(link)

        query = {'url': link, 'via.rewriter': rewriter}
        if extras:
            query.update(extras)

        url = url._replace(
            query=urlencode(query),
            path='/'.join(['html', doc_url.scheme, doc_url.hostname]) + doc_url.path
        )

        return url.geturl()

    @classmethod
    def legacy_via(cls, link):
        return f'http://localhost:9080/{link}'

    @classmethod
    def legacy_via_qa(cls, link):
        return f'https://qa-via.hypothes.is/{link}'
