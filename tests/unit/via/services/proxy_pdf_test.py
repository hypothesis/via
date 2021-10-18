import pytest
from h_matchers import Any

from via.requests_tools.error_handling import DEFAULT_ERROR_MAP
from via.services.proxy_pdf import ProxyPDFService, factory


class TestProxyPDFService:
    def test_factory(self):
        service = factory(None, None)

        assert isinstance(service, ProxyPDFService)

    def test_iter_url(self, service, requests, stream_bytes):
        stream_bytes.return_value = iter(range(3))

        result = list(service.iter_url("http://example.com/pdf"))

        requests.get.assert_called_once_with(
            url="http://example.com/pdf",
            headers={
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate",
                "User-Agent": "(gzip)",
                "X-Abuse-Policy": Any.string(),
                "X-Complaints-To": Any.string(),
            },
            stream=True,
            timeout=ProxyPDFService.TIMEOUT,
        )

        requests.get.return_value.raise_for_status.assert_called_once_with()
        assert result == [0, 1, 2]

    @pytest.mark.parametrize("original,raised", DEFAULT_ERROR_MAP.items())
    def test_iter_url_transforms_exceptions(self, service, requests, original, raised):
        requests.get.side_effect = original

        with pytest.raises(raised):
            list(service.iter_url("http://example.com/pdf"))

    def test_response_headers_adds_defaults(self, service):
        headers = service.response_headers()

        assert headers == {
            "Content-Disposition": "inline",
            "Content-Type": "application/pdf",
            "Cache-Control": "public, max-age=43200, stale-while-revalidate=86400",
        }

    def test_response_headers_overrides(self, service):
        headers = service.response_headers(
            {"Content-Disposition": "TEST", "Other-Header": "TEST"}
        )

        assert headers == {
            "Content-Disposition": "TEST",
            "Other-Header": "TEST",
            "Content-Type": "application/pdf",
            "Cache-Control": "public, max-age=43200, stale-while-revalidate=86400",
        }

    def test_request_headers_adds_defaults(self, service):
        headers = service.request_headers()

        assert headers == {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": "(gzip)",
            "X-Abuse-Policy": "https://web.hypothes.is/abuse-policy/",
            "X-Complaints-To": "https://web.hypothes.is/report-abuse/",
        }

    def test_request_headers_overrides(self, service):
        headers = service.request_headers({"Accept": "TEST", "Other-Header": "TEST"})

        assert headers == {
            "Accept": "TEST",
            "Other-Header": "TEST",
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": "(gzip)",
            "X-Abuse-Policy": "https://web.hypothes.is/abuse-policy/",
            "X-Complaints-To": "https://web.hypothes.is/report-abuse/",
        }

    @pytest.fixture
    def service(self):
        return ProxyPDFService()

    @pytest.fixture
    def stream_bytes(self, patch):
        return patch("via.services.proxy_pdf.stream_bytes")

    @pytest.fixture
    def requests(self, patch):
        return patch("via.services.proxy_pdf.requests")
