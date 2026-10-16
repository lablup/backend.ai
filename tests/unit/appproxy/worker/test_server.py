from __future__ import annotations

import datetime
import ipaddress
import ssl
from collections.abc import AsyncIterator
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

import aiohttp
import pytest
from aiohttp import web
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from ai.backend.appproxy.worker.server import http_client_pool_ctx
from ai.backend.appproxy.worker.types import RootContext
from ai.backend.common.clients.http_client.client_pool import ClientKey


@pytest.fixture
def self_signed_cert(tmp_path: Path) -> tuple[Path, Path]:
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1")])
    now = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=1))
        .not_valid_after(now + datetime.timedelta(hours=1))
        .add_extension(
            x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    cert_path = tmp_path / "cert.pem"
    key_path = tmp_path / "key.pem"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    return cert_path, key_path


@pytest.fixture
async def coordinator_endpoint(self_signed_cert: tuple[Path, Path]) -> AsyncIterator[str]:
    async def handle_ping(_: web.Request) -> web.Response:
        return web.Response(text="pong")

    app = web.Application()
    app.router.add_get("/ping", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain(*self_signed_cert)
    site = web.TCPSite(runner, "127.0.0.1", 0, ssl_context=ssl_ctx)
    await site.start()
    port = runner.addresses[0][1]
    try:
        yield f"https://127.0.0.1:{port}"
    finally:
        await runner.cleanup()


@pytest.fixture
def verify_ssl() -> bool:
    return True


@pytest.fixture
def root_context(verify_ssl: bool) -> MagicMock:
    root_ctx = MagicMock()
    root_ctx.local_config.proxy_worker.client_pool_cleanup_interval = 600
    root_ctx.local_config.proxy_worker.verify_coordinator_ssl_certificate = verify_ssl
    return root_ctx


@pytest.fixture
async def coordinator_session(
    root_context: MagicMock,
    coordinator_endpoint: str,
) -> AsyncIterator[aiohttp.ClientSession]:
    async with http_client_pool_ctx(cast(RootContext, root_context)):
        yield root_context.http_client_pool.load_client_session(
            ClientKey(endpoint=coordinator_endpoint, domain="coordinator")
        )


class TestHttpClientPoolCtxWithVerification:
    async def test_rejects_untrusted_certificate(
        self,
        coordinator_session: aiohttp.ClientSession,
    ) -> None:
        with pytest.raises(aiohttp.ClientConnectorCertificateError):
            await coordinator_session.get("/ping")


class TestHttpClientPoolCtxWithoutVerification:
    @pytest.fixture
    def verify_ssl(self) -> bool:
        return False

    async def test_accepts_untrusted_certificate(
        self,
        coordinator_session: aiohttp.ClientSession,
    ) -> None:
        async with coordinator_session.get("/ping") as resp:
            assert resp.status == 200
