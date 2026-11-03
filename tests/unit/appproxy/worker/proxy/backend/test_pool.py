from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from ai.backend.appproxy.common.errors import WorkerNotAvailable
from ai.backend.appproxy.worker.proxy.backend.pool import RoutePool, RoutePoolSpec
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    IngressBackend,
    IngressBackendID,
    IngressTargetGroup,
    IngressTargetGroupID,
    SessionIngressTarget,
)
from ai.backend.common.types import SessionId

_GROUP_ID = IngressTargetGroupID("00000000-0000-0000-0000-000000000000")
_BACKEND_ID = IngressBackendID("00000000-0000-0000-0000-000000000000")
_TARGET_A = SessionIngressTarget(
    host="10.0.0.1",
    port=8000,
    session_id=SessionId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")),
)
_TARGET_B = SessionIngressTarget(
    host="10.0.0.2",
    port=8000,
    session_id=SessionId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")),
)
_TARGET_A_MOVED = _TARGET_A.model_copy(update={"host": "10.0.0.9"})
_SPEC = RoutePoolSpec(failure_threshold=1, health_check_interval=3600.0)
_PROBED_SESSION_ID = SessionId(UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"))
_PROBES_TO_RECEIVE = 3


@dataclass(frozen=True)
class _HttpProbeCase:
    status_answered_at_health_check_path: int
    health_check: ModelHealthCheck


@dataclass(frozen=True)
class _TcpProbeCase:
    health_check: ModelHealthCheck | None


@dataclass(frozen=True)
class _PoolProbingOneTarget:
    pool: RoutePool
    target: SessionIngressTarget
    probes_received: asyncio.Event


class TestRoutePool:
    @pytest.fixture
    async def pool_with_a_weighted_and_an_unweighted_group(self) -> AsyncIterator[RoutePool]:
        pool = RoutePool(
            IngressBackend(
                id=_BACKEND_ID,
                target_groups=[
                    IngressTargetGroup(id=_GROUP_ID, weight=0, targets=[_TARGET_A]),
                    IngressTargetGroup(id=_GROUP_ID, weight=100, targets=[_TARGET_B]),
                ],
            ),
            spec=_SPEC,
        )
        yield pool
        await pool.close()

    @pytest.fixture
    async def pool_holding_target_a_marked_unhealthy(self) -> AsyncIterator[RoutePool]:
        pool = RoutePool(
            IngressBackend(
                id=_BACKEND_ID,
                target_groups=[IngressTargetGroup(id=_GROUP_ID, weight=100, targets=[_TARGET_A])],
            ),
            spec=_SPEC,
        )
        pool.record_failure(_TARGET_A)
        yield pool
        await pool.close()

    @pytest.fixture
    async def pool_probing_a_target_over_http(
        self, case: _HttpProbeCase
    ) -> AsyncIterator[_PoolProbingOneTarget]:
        probe_count = 0
        probes_received = asyncio.Event()

        async def answer_probe(_request: web.Request) -> web.Response:
            nonlocal probe_count
            probe_count += 1
            if probe_count >= _PROBES_TO_RECEIVE:
                probes_received.set()
            return web.Response(status=case.status_answered_at_health_check_path)

        app = web.Application()
        app.router.add_get(case.health_check.path, answer_probe)
        server = TestServer(app, host="127.0.0.1")
        await server.start_server()
        assert server.port is not None
        target = SessionIngressTarget(
            host="127.0.0.1", port=server.port, session_id=_PROBED_SESSION_ID
        )
        pool = RoutePool(
            IngressBackend(
                id=_BACKEND_ID,
                target_groups=[IngressTargetGroup(id=_GROUP_ID, weight=100, targets=[target])],
                health_check=case.health_check,
            ),
            spec=_SPEC,
        )
        yield _PoolProbingOneTarget(pool=pool, target=target, probes_received=probes_received)
        await pool.close()
        await server.close()

    @pytest.fixture
    async def pool_probing_a_target_that_accepts_tcp_and_never_answers_http(
        self, case: _TcpProbeCase
    ) -> AsyncIterator[_PoolProbingOneTarget]:
        connection_count = 0
        probes_received = asyncio.Event()

        async def close_connection(
            _reader: asyncio.StreamReader, writer: asyncio.StreamWriter
        ) -> None:
            nonlocal connection_count
            connection_count += 1
            if connection_count >= _PROBES_TO_RECEIVE:
                probes_received.set()
            writer.close()

        server = await asyncio.start_server(close_connection, host="127.0.0.1", port=0)
        port = server.sockets[0].getsockname()[1]
        target = SessionIngressTarget(host="127.0.0.1", port=port, session_id=_PROBED_SESSION_ID)
        pool = RoutePool(
            IngressBackend(
                id=_BACKEND_ID,
                target_groups=[IngressTargetGroup(id=_GROUP_ID, weight=100, targets=[target])],
                health_check=case.health_check,
            ),
            spec=RoutePoolSpec(failure_threshold=1, health_check_interval=0.01),
        )
        yield _PoolProbingOneTarget(pool=pool, target=target, probes_received=probes_received)
        await pool.close()
        server.close()
        await server.wait_closed()

    async def test_select_skips_a_group_with_no_weight(
        self, pool_with_a_weighted_and_an_unweighted_group: RoutePool
    ) -> None:
        assert await pool_with_a_weighted_and_an_unweighted_group.select() == _TARGET_B

    async def test_update_keeps_the_health_of_a_target_at_the_same_address(
        self, pool_holding_target_a_marked_unhealthy: RoutePool
    ) -> None:
        pool = pool_holding_target_a_marked_unhealthy
        await pool.update(
            IngressBackend(
                id=_BACKEND_ID,
                target_groups=[IngressTargetGroup(id=_GROUP_ID, weight=100, targets=[_TARGET_A])],
            )
        )
        with pytest.raises(WorkerNotAvailable):
            await pool.select()

    async def test_update_starts_a_target_moved_to_a_new_address_healthy(
        self, pool_holding_target_a_marked_unhealthy: RoutePool
    ) -> None:
        pool = pool_holding_target_a_marked_unhealthy
        await pool.update(
            IngressBackend(
                id=_BACKEND_ID,
                target_groups=[
                    IngressTargetGroup(id=_GROUP_ID, weight=100, targets=[_TARGET_A_MOVED])
                ],
            )
        )
        assert await pool.select() == _TARGET_A_MOVED

    async def test_update_drops_a_target_missing_from_the_backend(
        self, pool_holding_target_a_marked_unhealthy: RoutePool
    ) -> None:
        pool = pool_holding_target_a_marked_unhealthy
        await pool.update(
            IngressBackend(
                id=_BACKEND_ID,
                target_groups=[IngressTargetGroup(id=_GROUP_ID, weight=100, targets=[_TARGET_B])],
            )
        )
        assert await pool.select() == _TARGET_B

    @pytest.mark.parametrize(
        "case",
        [
            _HttpProbeCase(
                status_answered_at_health_check_path=204,
                health_check=ModelHealthCheck(
                    enable=True,
                    path="/ready",
                    interval=0.01,
                    expected_status_code=204,
                    max_retries=1,
                ),
            ),
            _HttpProbeCase(
                status_answered_at_health_check_path=503,
                health_check=ModelHealthCheck(
                    enable=True,
                    path="/ready",
                    interval=0.01,
                    expected_status_code=204,
                    max_retries=100,
                ),
            ),
        ],
        ids=lambda case: (
            f"answers {case.status_answered_at_health_check_path}"
            f" with max_retries {case.health_check.max_retries}"
        ),
    )
    async def test_http_probed_target_stays_selectable_while_failed_probes_are_fewer_than_max_retries(
        self, pool_probing_a_target_over_http: _PoolProbingOneTarget
    ) -> None:
        situation = pool_probing_a_target_over_http
        await asyncio.wait_for(situation.probes_received.wait(), timeout=5.0)
        assert await situation.pool.select() == situation.target

    @pytest.mark.parametrize(
        "case",
        [
            _HttpProbeCase(
                status_answered_at_health_check_path=503,
                health_check=ModelHealthCheck(
                    enable=True,
                    path="/ready",
                    interval=0.01,
                    expected_status_code=204,
                    max_retries=2,
                ),
            ),
        ],
        ids=lambda case: f"answers {case.status_answered_at_health_check_path}",
    )
    async def test_http_probed_target_is_not_selected_once_max_retries_probes_fail(
        self, pool_probing_a_target_over_http: _PoolProbingOneTarget
    ) -> None:
        situation = pool_probing_a_target_over_http
        await asyncio.wait_for(situation.probes_received.wait(), timeout=5.0)
        with pytest.raises(WorkerNotAvailable):
            await situation.pool.select()

    @pytest.mark.parametrize(
        "case",
        [
            _TcpProbeCase(health_check=None),
            _TcpProbeCase(
                health_check=ModelHealthCheck(
                    enable=False, path="/ready", interval=0.01, max_retries=1
                ),
            ),
        ],
        ids=lambda case: "no health check" if case.health_check is None else "disabled",
    )
    async def test_target_without_an_enabled_health_check_is_probed_by_tcp_connect(
        self,
        pool_probing_a_target_that_accepts_tcp_and_never_answers_http: _PoolProbingOneTarget,
    ) -> None:
        situation = pool_probing_a_target_that_accepts_tcp_and_never_answers_http
        await asyncio.wait_for(situation.probes_received.wait(), timeout=5.0)
        assert await situation.pool.select() == situation.target
