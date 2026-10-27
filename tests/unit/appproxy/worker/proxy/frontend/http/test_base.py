from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_mock
from aiohttp import hdrs, web
from aiohttp.test_utils import make_mocked_request
from multidict import CIMultiDict

from ai.backend.appproxy.common.config import ContentEncodingConfig
from ai.backend.appproxy.common.errors.http import UnsupportedContentEncoding
from ai.backend.appproxy.worker.proxy.frontend.http.port import PortFrontend


@dataclass(frozen=True)
class _ContentEncodingHeaders:
    values: tuple[str, ...]


@pytest.fixture
def port_frontend_rejecting_br_and_zstd(mocker: pytest_mock.MockerFixture) -> PortFrontend:
    root_context = mocker.MagicMock()
    root_context.content_encoding = ContentEncodingConfig(rejected_encodings=["br", "zstd"])
    return PortFrontend(root_context=root_context)


@pytest.fixture
def port_frontend_rejecting_no_encoding(mocker: pytest_mock.MockerFixture) -> PortFrontend:
    root_context = mocker.MagicMock()
    root_context.content_encoding = ContentEncodingConfig()
    return PortFrontend(root_context=root_context)


@pytest.fixture
def http_backend() -> MagicMock:
    return MagicMock(proxy_http=AsyncMock(return_value=web.Response()))


@pytest.fixture
def request_with_content_encoding(
    request: pytest.FixtureRequest,
    http_backend: MagicMock,
) -> web.Request:
    headers: _ContentEncodingHeaders = request.param
    proxied_request = make_mocked_request(
        "POST",
        "/",
        headers=CIMultiDict((hdrs.CONTENT_ENCODING, value) for value in headers.values),
    )
    proxied_request["backend"] = http_backend
    return proxied_request


class TestBaseHTTPFrontendProxy:
    @pytest.mark.parametrize(
        "request_with_content_encoding",
        [
            _ContentEncodingHeaders(values=("br",)),
            _ContentEncodingHeaders(values=("gzip, br",)),
            _ContentEncodingHeaders(values=("gzip", "br")),
            _ContentEncodingHeaders(values=("zstd",)),
        ],
        ids=lambda headers: " + ".join(headers.values),
        indirect=True,
    )
    async def test_rejects_request_with_rejected_encoding_without_forwarding(
        self,
        port_frontend_rejecting_br_and_zstd: PortFrontend,
        http_backend: MagicMock,
        request_with_content_encoding: web.Request,
    ) -> None:
        with pytest.raises(UnsupportedContentEncoding):
            await port_frontend_rejecting_br_and_zstd.proxy(request_with_content_encoding)

        http_backend.proxy_http.assert_not_awaited()

    @pytest.mark.parametrize(
        "request_with_content_encoding",
        [
            _ContentEncodingHeaders(values=()),
            _ContentEncodingHeaders(values=("gzip",)),
            _ContentEncodingHeaders(values=("deflate",)),
            _ContentEncodingHeaders(values=("identity",)),
            _ContentEncodingHeaders(values=("BR",)),
        ],
        ids=lambda headers: " + ".join(headers.values) or "none",
        indirect=True,
    )
    async def test_forwards_request_without_rejected_encoding(
        self,
        port_frontend_rejecting_br_and_zstd: PortFrontend,
        http_backend: MagicMock,
        request_with_content_encoding: web.Request,
    ) -> None:
        await port_frontend_rejecting_br_and_zstd.proxy(request_with_content_encoding)

        http_backend.proxy_http.assert_awaited_once_with(request_with_content_encoding)

    @pytest.mark.parametrize(
        "request_with_content_encoding",
        [
            _ContentEncodingHeaders(values=("br",)),
            _ContentEncodingHeaders(values=("gzip, br",)),
            _ContentEncodingHeaders(values=("gzip",)),
            _ContentEncodingHeaders(values=()),
        ],
        ids=lambda headers: " + ".join(headers.values) or "none",
        indirect=True,
    )
    async def test_forwards_every_request_when_no_encoding_is_rejected(
        self,
        port_frontend_rejecting_no_encoding: PortFrontend,
        http_backend: MagicMock,
        request_with_content_encoding: web.Request,
    ) -> None:
        await port_frontend_rejecting_no_encoding.proxy(request_with_content_encoding)

        http_backend.proxy_http.assert_awaited_once_with(request_with_content_encoding)
