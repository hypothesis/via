from unittest.mock import sentinel

import pytest
from freezegun import freeze_time

from via.exceptions import UpstreamServiceError
from via.requests_tools.headers import add_request_headers
from via.services.jstor import JSTORAPI, factory


class TestJSTORAPI:
    @pytest.mark.parametrize(
        "api_url,expected", [(None, False), ("http://jstor-api.com", True)]
    )
    def test_enabled(self, api_url, expected):
        svc = JSTORAPI(
            api_url=api_url, http_service=sentinel.http, secret=sentinel.secret
        )

        assert svc.enabled == expected

    @pytest.mark.parametrize(
        "url,is_jstor", (("jstor://anything", True), ("http://example.com", False))
    )
    def test_is_jstor_url(self, url, is_jstor):
        assert JSTORAPI.is_jstor_url(url) == is_jstor

    @pytest.mark.parametrize(
        "url,expected",
        [
            (
                "jstor://ARTICLE_ID",
                "http://jstor.example.com/pdf-url/10.2307/ARTICLE_ID",
            ),
            ("jstor://PREFIX/SUFFIX", "http://jstor.example.com/pdf-url/PREFIX/SUFFIX"),
        ],
    )
    @freeze_time("2022-01-14")
    def test_get_public_url(self, svc, jwt, http_service, url, expected):
        jwt.encode.return_value = "TOKEN"

        public_url = svc.get_public_url(url=url, site_code=sentinel.site_code)

        jwt.encode.assert_called_once_with(
            {"exp": 1642122000, "site_code": sentinel.site_code},
            sentinel.secret,
            algorithm="HS256",
        )

        http_service.request.assert_called_once_with(
            method="GET",
            url=expected,
            headers=add_request_headers({"Authorization": "Bearer TOKEN"}),
        )

        assert public_url == http_service.request.return_value.text

    def test_get_public_url_with_bad_return_value_from_s3(self, svc, http_service):
        http_service.request.return_value.text = "NOT A URL"

        with pytest.raises(UpstreamServiceError):
            svc.get_public_url(url="jstor://ANY", site_code=sentinel.site_code)

    @pytest.fixture
    def svc(self, http_service):
        return JSTORAPI(
            api_url="http://jstor.example.com",
            http_service=http_service,
            secret=sentinel.secret,
        )

    @pytest.fixture(autouse=True)
    def jwt(self, patch):
        return patch("via.services.jstor.jwt")


class TestFactory:
    def test_it(self, pyramid_request, JSTORAPI, http_service):
        pyramid_request.registry.settings["jstor_api_url"] = sentinel.jstor_api_url
        pyramid_request.registry.settings[
            "jstor_api_secret"
        ] = sentinel.jstor_api_secret

        svc = factory(sentinel.context, pyramid_request)

        JSTORAPI.assert_called_once_with(
            http_service=http_service,
            api_url=sentinel.jstor_api_url,
            secret=sentinel.jstor_api_secret,
        )
        assert svc == JSTORAPI.return_value

    @pytest.fixture
    def JSTORAPI(self, patch):
        return patch("via.services.jstor.JSTORAPI")
