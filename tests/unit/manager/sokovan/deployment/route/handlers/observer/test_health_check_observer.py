"""Tests for RouteHealthObserver interval throttle and consecutive-failure counting."""

from __future__ import annotations

import ssl
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from dateutil.tz import tzutc

from ai.backend.common.clients.valkey_client.valkey_schedule.types import (
    ReplicaHealthResult,
    ReplicaHealthStatus,
    ReplicaProbeTarget,
)
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.types import EndpointProtocol, SessionId
from ai.backend.manager.data.deployment.types import (
    RouteData,
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.sokovan.deployment.route.handlers.observer.health_check import (
    RouteHealthObserver,
)

_NOW = 1000


def _make_route(health_check: ModelHealthCheck | None) -> RouteData:
    return RouteData(
        route_id=ReplicaID(uuid4()),
        deployment_id=DeploymentID(uuid4()),
        session_id=SessionId(uuid4()),
        status=RouteStatus.RUNNING,
        health_status=RouteHealthStatus.HEALTHY,
        traffic_ratio=1.0,
        created_at=datetime.fromtimestamp(0, tz=tzutc()),
        revision_id=DeploymentRevisionID(uuid4()),
        traffic_status=RouteTrafficStatus.ACTIVE,
        health_check=health_check,
        termination_grace_period=30.0,
        replica_host="10.0.0.1",
        replica_port=8000,
    )


def _probe_target(route: RouteData) -> ReplicaProbeTarget:
    assert route.health_check is not None
    return ReplicaProbeTarget(
        replica_id=route.route_id,
        health_path=route.health_check.path,
        inference_port=route.replica_port or 8000,
        replica_host=route.replica_host or "10.0.0.1",
    )


def _make_valkey(
    *,
    probe_targets: Mapping[ReplicaID, ReplicaProbeTarget],
    statuses: Mapping[ReplicaID, ReplicaHealthStatus | None],
    now: int = _NOW,
) -> AsyncMock:
    valkey = AsyncMock()
    valkey.get_route_probe_targets_batch.return_value = probe_targets
    valkey.get_route_health_statuses_batch.return_value = statuses
    valkey.get_redis_time.return_value = now
    valkey.record_route_health_statuses_batch.return_value = None
    return valkey


def _observer(valkey: AsyncMock) -> RouteHealthObserver:
    return RouteHealthObserver(deployment_repository=AsyncMock(), valkey_schedule=valkey)


def _recorded(valkey: AsyncMock) -> list[ReplicaHealthResult]:
    return cast(
        "list[ReplicaHealthResult]",
        valkey.record_route_health_statuses_batch.call_args[0][0],
    )


class TestRouteHealthObserverCounting:
    async def test_first_probe_success_records_zero_failures(self) -> None:
        check = ModelHealthCheck(enable=True, interval=10.0)
        route = _make_route(check)
        valkey = _make_valkey(
            probe_targets={route.route_id: _probe_target(route)},
            statuses={route.route_id: None},
        )
        observer = _observer(valkey)
        observer._http_health_check = AsyncMock(return_value=True)  # type: ignore[method-assign]

        result = await observer.observe([route])

        assert result.observed_count == 1
        recorded = _recorded(valkey)
        assert recorded[0].healthy is True
        assert recorded[0].consecutive_failures == 0
        assert recorded[0].ttl_sec == check.health_status_ttl_sec()

    async def test_failure_increments_previous_count(self) -> None:
        route = _make_route(ModelHealthCheck(enable=True, interval=10.0))
        statuses = {
            route.route_id: ReplicaHealthStatus(
                replica_id=route.route_id,
                healthy=False,
                last_check=_NOW - 20,  # due: 20 >= interval 10
                consecutive_failures=2,
            )
        }
        valkey = _make_valkey(
            probe_targets={route.route_id: _probe_target(route)},
            statuses=statuses,
        )
        observer = _observer(valkey)
        observer._http_health_check = AsyncMock(return_value=False)  # type: ignore[method-assign]

        await observer.observe([route])

        recorded = _recorded(valkey)
        assert recorded[0].healthy is False
        assert recorded[0].consecutive_failures == 3

    async def test_success_resets_count(self) -> None:
        route = _make_route(ModelHealthCheck(enable=True, interval=10.0))
        statuses = {
            route.route_id: ReplicaHealthStatus(
                replica_id=route.route_id,
                healthy=False,
                last_check=_NOW - 20,
                consecutive_failures=5,
            )
        }
        valkey = _make_valkey(
            probe_targets={route.route_id: _probe_target(route)},
            statuses=statuses,
        )
        observer = _observer(valkey)
        observer._http_health_check = AsyncMock(return_value=True)  # type: ignore[method-assign]

        await observer.observe([route])

        assert _recorded(valkey)[0].consecutive_failures == 0


class TestRouteHealthObserverThrottle:
    async def test_skips_probe_within_interval(self) -> None:
        route = _make_route(ModelHealthCheck(enable=True, interval=10.0))
        statuses = {
            route.route_id: ReplicaHealthStatus(
                replica_id=route.route_id,
                healthy=True,
                last_check=_NOW - 5,  # not due: 5 < interval 10
                consecutive_failures=0,
            )
        }
        valkey = _make_valkey(
            probe_targets={route.route_id: _probe_target(route)},
            statuses=statuses,
        )
        observer = _observer(valkey)
        observer._http_health_check = AsyncMock(return_value=True)  # type: ignore[method-assign]

        result = await observer.observe([route])

        assert result.observed_count == 0
        observer._http_health_check.assert_not_called()
        valkey.record_route_health_statuses_batch.assert_not_called()

    async def test_skips_route_without_probe_target(self) -> None:
        route = _make_route(ModelHealthCheck(enable=True, interval=10.0))
        valkey = _make_valkey(probe_targets={}, statuses={route.route_id: None})
        observer = _observer(valkey)
        observer._http_health_check = AsyncMock(return_value=True)  # type: ignore[method-assign]

        result = await observer.observe([route])

        assert result.observed_count == 0
        observer._http_health_check.assert_not_called()

    async def test_skips_disabled_health_check(self) -> None:
        """A route whose health_check has enable=False is not probed."""
        route = _make_route(ModelHealthCheck(enable=False, interval=10.0))
        valkey = _make_valkey(
            probe_targets={route.route_id: _probe_target(route)},
            statuses={route.route_id: None},
        )
        observer = _observer(valkey)
        observer._http_health_check = AsyncMock(return_value=True)  # type: ignore[method-assign]

        result = await observer.observe([route])

        assert result.observed_count == 0
        observer._http_health_check.assert_not_called()
        valkey.record_route_health_statuses_batch.assert_not_called()


class TestRouteHealthObserverProbePolicy:
    async def test_probe_uses_per_route_timeout_and_status_code(self) -> None:
        route = _make_route(
            ModelHealthCheck(
                enable=True,
                interval=10.0,
                max_wait_time=42.0,
                expected_status_code=204,
                path="/livez",
            )
        )
        valkey = _make_valkey(
            probe_targets={route.route_id: _probe_target(route)},
            statuses={route.route_id: None},
        )
        observer = _observer(valkey)
        observer._http_health_check = AsyncMock(return_value=True)  # type: ignore[method-assign]

        await observer.observe([route])

        call = observer._http_health_check.call_args
        assert call.args == (
            route.route_id,
            "10.0.0.1",
            8000,
            "/livez",
            42.0,
            204,
            EndpointProtocol.HTTP,
        )

    async def test_probe_passes_target_protocol(self) -> None:
        route = _make_route(ModelHealthCheck(enable=True, interval=10.0))
        target = _probe_target(route)
        target.protocol = EndpointProtocol.TCP
        valkey = _make_valkey(
            probe_targets={route.route_id: target},
            statuses={route.route_id: None},
        )
        observer = _observer(valkey)
        observer._http_health_check = AsyncMock(return_value=True)  # type: ignore[method-assign]

        await observer.observe([route])

        assert observer._http_health_check.call_args.args[-1] is EndpointProtocol.TCP


@dataclass
class _Replica:
    host: str
    port: int
    received_paths: list[str] = field(default_factory=list)


def _self_signed_server_context(tmp_path: Path) -> ssl.SSLContext:
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "replica.invalid")])
    now = datetime.now(tz=tzutc())
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(hours=1))
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
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain(cert_path, key_path)
    return ctx


async def _serve_replica(ssl_context: ssl.SSLContext | None) -> AsyncIterator[_Replica]:
    replica = _Replica(host="127.0.0.1", port=0)

    async def handle(request: web.Request) -> web.Response:
        replica.received_paths.append(request.raw_path)
        if request.path == "/redirect":
            return web.Response(status=302, headers={"Location": "/health"})
        return web.Response()

    app = web.Application()
    app.router.add_route("GET", "/{tail:.*}", handle)
    server = TestServer(app, host=replica.host)
    await server.start_server(ssl=ssl_context)
    replica.port = server.port or 0
    try:
        yield replica
    finally:
        await server.close()


@pytest.fixture
async def replica() -> AsyncIterator[_Replica]:
    """A local HTTP server standing in for the replica; ``/redirect`` answers 302 to ``/health``."""
    async for served in _serve_replica(None):
        yield served


@pytest.fixture
async def tls_replica(tmp_path: Path) -> AsyncIterator[_Replica]:
    """The same replica behind TLS with a self-signed certificate."""
    async for served in _serve_replica(_self_signed_server_context(tmp_path)):
        yield served


class TestRouteHealthObserverHttpProbe:
    @pytest.mark.parametrize("path", ["/health?x=1", "/a@other.host/x"])
    async def test_probe_stays_on_replica_host(self, replica: _Replica, path: str) -> None:
        observer = _observer(_make_valkey(probe_targets={}, statuses={}))

        healthy = await observer._http_health_check(
            ReplicaID(uuid4()), replica.host, replica.port, path, 5.0, 200, EndpointProtocol.HTTP
        )

        assert healthy is True
        assert replica.received_paths == [path]

    async def test_probe_does_not_follow_redirect(self, replica: _Replica) -> None:
        observer = _observer(_make_valkey(probe_targets={}, statuses={}))

        healthy = await observer._http_health_check(
            ReplicaID(uuid4()),
            replica.host,
            replica.port,
            "/redirect",
            5.0,
            200,
            EndpointProtocol.HTTP,
        )

        assert healthy is False
        assert replica.received_paths == ["/redirect"]

    async def test_path_that_replaces_host_fails_without_request(self, replica: _Replica) -> None:
        # Joined as a string, this path would move the probe to the host after ``@``.
        # The local server stands in for that host, so a regression shows up as a request it receives.
        observer = _observer(_make_valkey(probe_targets={}, statuses={}))
        path = f"@{replica.host}:{replica.port}/x"

        healthy = await observer._http_health_check(
            ReplicaID(uuid4()), "192.0.2.1", 9, path, 5.0, 200, EndpointProtocol.HTTP
        )

        assert healthy is False
        assert replica.received_paths == []


class TestRouteHealthObserverTlsProbe:
    async def test_tcp_probe_accepts_self_signed_certificate(self, tls_replica: _Replica) -> None:
        observer = _observer(_make_valkey(probe_targets={}, statuses={}))

        healthy = await observer._http_health_check(
            ReplicaID(uuid4()),
            tls_replica.host,
            tls_replica.port,
            "/health",
            5.0,
            200,
            EndpointProtocol.TCP,
        )

        assert healthy is True
        assert tls_replica.received_paths == ["/health"]

    async def test_http_probe_fails_against_tls_replica(self, tls_replica: _Replica) -> None:
        observer = _observer(_make_valkey(probe_targets={}, statuses={}))

        healthy = await observer._http_health_check(
            ReplicaID(uuid4()),
            tls_replica.host,
            tls_replica.port,
            "/health",
            5.0,
            200,
            EndpointProtocol.HTTP,
        )

        assert healthy is False
        assert tls_replica.received_paths == []

    async def test_tcp_probe_fails_against_plain_replica(self, replica: _Replica) -> None:
        observer = _observer(_make_valkey(probe_targets={}, statuses={}))

        healthy = await observer._http_health_check(
            ReplicaID(uuid4()),
            replica.host,
            replica.port,
            "/health",
            5.0,
            200,
            EndpointProtocol.TCP,
        )

        assert healthy is False
        assert replica.received_paths == []
