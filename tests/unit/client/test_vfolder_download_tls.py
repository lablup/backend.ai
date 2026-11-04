from __future__ import annotations

import ssl
from pathlib import Path
from uuid import UUID

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer
from pytest_aiohttp import AiohttpServer

from ai.backend.client.config import APIConfig
from ai.backend.client.session import AsyncSession

_VFOLDER_ID = UUID(int=1)
_FILE_NAME = "model.bin"
_FILE_CONTENT = b"file content"


@pytest.fixture
async def manager_issuing_self_signed_download_url(
    aiohttp_server: AiohttpServer,
    self_signed_tls_context: ssl.SSLContext,
) -> TestServer:
    async def _serve_file(_request: web.Request) -> web.Response:
        return web.Response(body=_FILE_CONTENT)

    storage_proxy_app = web.Application()
    storage_proxy_app.router.add_get("/download", _serve_file)
    storage_proxy = await aiohttp_server(storage_proxy_app, ssl=self_signed_tls_context)

    async def _report_api_version(_request: web.Request) -> web.Response:
        return web.json_response({"version": "v9.20250722", "manager": "test"})

    async def _issue_download_url(_request: web.Request) -> web.Response:
        return web.json_response({
            "url": str(storage_proxy.make_url("/download")),
            "token": "download-token",
        })

    manager_app = web.Application()
    manager_app.router.add_get("/", _report_api_version)
    manager_app.router.add_post(
        f"/folders/{_VFOLDER_ID.hex}/request-download",
        _issue_download_url,
    )
    return await aiohttp_server(manager_app)


@pytest.fixture
def isolated_home_without_tls_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("BACKEND_SKIP_SSLCERT_VALIDATION", raising=False)


@pytest.fixture
def config_verifying_tls(
    manager_issuing_self_signed_download_url: TestServer,
    isolated_home_without_tls_override: None,
) -> APIConfig:
    return APIConfig(
        endpoint=str(manager_issuing_self_signed_download_url.make_url("/")),
        endpoint_type="api",
        access_key="access-key",
        secret_key="secret-key",
    )


@pytest.fixture
def config_skipping_tls_validation(
    manager_issuing_self_signed_download_url: TestServer,
    isolated_home_without_tls_override: None,
) -> APIConfig:
    return APIConfig(
        endpoint=str(manager_issuing_self_signed_download_url.make_url("/")),
        endpoint_type="api",
        access_key="access-key",
        secret_key="secret-key",
        skip_sslcert_validation=True,
    )


class TestVFolderDownloadTLS:
    async def test_untrusted_certificate_fails_by_default(
        self,
        config_verifying_tls: APIConfig,
        tmp_path: Path,
    ) -> None:
        async with AsyncSession(config=config_verifying_tls) as session:
            with pytest.raises(RuntimeError, match=_FILE_NAME):
                await session.VFolder("folder", id=_VFOLDER_ID).download(
                    [_FILE_NAME], basedir=tmp_path, max_retries=1
                )

        assert not (tmp_path / _FILE_NAME).exists()

    async def test_untrusted_certificate_passes_with_skip_sslcert_validation(
        self,
        config_skipping_tls_validation: APIConfig,
        tmp_path: Path,
    ) -> None:
        async with AsyncSession(config=config_skipping_tls_validation) as session:
            await session.VFolder("folder", id=_VFOLDER_ID).download(
                [_FILE_NAME], basedir=tmp_path, max_retries=1
            )

        assert (tmp_path / _FILE_NAME).read_bytes() == _FILE_CONTENT
