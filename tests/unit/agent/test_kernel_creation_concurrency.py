from __future__ import annotations

import asyncio
import functools
import uuid
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from callosum.rpc import RPCMessage
from callosum.rpc.message import RPCMessageTypes

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.errors.resources import ResourceError
from ai.backend.agent.server import AgentRPCServer
from ai.backend.common.types import AgentId, KernelId, SessionId


class _CreationTracker:
    """Stands in for `AbstractAgent.create_kernel`, recording how many creations overlap."""

    active: int
    peak: int
    finished: int
    semas: list[asyncio.Semaphore]

    def __init__(self) -> None:
        self.active = 0
        self.peak = 0
        self.finished = 0
        self.semas = []

    async def create_kernel(
        self,
        ownership_data: Any,
        kernel_image: Any,
        kernel_config: Any,
        cluster_info: Any,
        *,
        throttle_sema: asyncio.Semaphore,
    ) -> dict[str, Any]:
        self.semas.append(throttle_sema)
        async with throttle_sema:
            self.active += 1
            self.peak = max(self.peak, self.active)
            await asyncio.sleep(0.01)
            self.active -= 1
        self.finished += 1
        return {
            "id": ownership_data.kernel_id,
            "kernel_host": "127.0.0.1",
            "repl_in_port": 2000,
            "repl_out_port": 2001,
            "stdin_port": 2002,
            "stdout_port": 2003,
            "service_ports": [],
            "container_id": "c",
            "resource_spec": {},
            "attached_devices": {},
            "agent_addr": "tcp://127.0.0.1:6001",
            "scaling_group": "default",
        }


def _agent(concurrency: int, tracker: _CreationTracker) -> MagicMock:
    agent = MagicMock()
    agent.id = AgentId("i-test")
    agent.local_config.agent.kernel_creation_concurrency = concurrency
    agent.kernel_creation_sema = asyncio.Semaphore(concurrency)
    agent.create_kernel = tracker.create_kernel
    agent.produce_error_event = AsyncMock()
    return agent


def _server(agent: MagicMock) -> AgentRPCServer:
    server = MagicMock()
    server.runtime.get_agent.return_value = agent
    server.error_monitor.capture_exception = AsyncMock()
    return cast(AgentRPCServer, server)


async def _create_kernels(server: AgentRPCServer, num_kernels: int) -> Any:
    kernel_ids = [uuid.uuid4() for _ in range(num_kernels)]
    image_ref = MagicMock()
    image_ref.canonical = "cr.backend.ai/stable/python:latest"
    args: tuple[Any, ...] = (
        str(uuid.uuid4()),
        [str(k) for k in kernel_ids],
        [{} for _ in kernel_ids],
        {},
        dict.fromkeys(kernel_ids, image_ref),
    )
    request = RPCMessage(
        None,
        RPCMessageTypes.FUNCTION,
        "create_kernels",
        "",
        0,
        None,
        {"args": args, "kwargs": {}},
    )
    return await AgentRPCServer.create_kernels(server, request)


@pytest.fixture
def tracker() -> _CreationTracker:
    return _CreationTracker()


class TestKernelCreationConcurrency:
    async def test_concurrent_requests_share_the_agent_bound(
        self, tracker: _CreationTracker
    ) -> None:
        server = _server(_agent(2, tracker))

        await asyncio.gather(_create_kernels(server, 2), _create_kernels(server, 2))

        assert tracker.finished == 4
        assert tracker.peak == 2

    async def test_every_creation_is_throttled_by_the_agents_own_semaphore(
        self, tracker: _CreationTracker
    ) -> None:
        agent = _agent(2, tracker)
        server = _server(agent)

        await asyncio.gather(_create_kernels(server, 3), _create_kernels(server, 1))

        assert len(tracker.semas) == 4
        assert all(sema is agent.kernel_creation_sema for sema in tracker.semas)
        assert not agent.kernel_creation_sema.locked()


class _CreateWentAhead(Exception):
    """Raised by the first step past the guard, so a test stops there."""


class TestCreateForARegisteredKernel:
    @pytest.fixture
    def kernel_id(self) -> KernelId:
        return KernelId(uuid.uuid4())

    @pytest.fixture
    def agent(self) -> MagicMock:
        agent = MagicMock()
        agent._active_creates = {}
        agent.track_create = functools.partial(AbstractAgent.track_create, agent)
        agent.kernel_registry = {}
        agent.anycast_and_broadcast_event = AsyncMock()
        agent.init_kernel_context = AsyncMock(side_effect=_CreateWentAhead)
        return agent

    async def _create(self, agent: MagicMock, kernel_id: KernelId, *, restarting: bool) -> None:
        ownership_data = MagicMock(kernel_id=kernel_id, session_id=SessionId(uuid.uuid4()))
        await AbstractAgent.create_kernel(
            agent,
            ownership_data,
            MagicMock(),
            cast(Any, {}),
            cast(Any, {}),
            restarting=restarting,
        )

    async def test_a_retried_create_keeps_the_live_kernel_and_its_runner(
        self, agent: MagicMock, kernel_id: KernelId
    ) -> None:
        live_kernel = MagicMock()
        agent.kernel_registry[kernel_id] = live_kernel

        with pytest.raises(ResourceError):
            await self._create(agent, kernel_id, restarting=False)

        assert agent.kernel_registry[kernel_id] is live_kernel
        agent.init_kernel_context.assert_not_called()

    async def test_a_restart_goes_ahead_over_the_kernel_it_restarts(
        self, agent: MagicMock, kernel_id: KernelId
    ) -> None:
        agent.kernel_registry[kernel_id] = MagicMock()

        with pytest.raises(_CreateWentAhead):
            await self._create(agent, kernel_id, restarting=True)

    async def test_a_new_kernel_goes_ahead(self, agent: MagicMock, kernel_id: KernelId) -> None:
        with pytest.raises(_CreateWentAhead):
            await self._create(agent, kernel_id, restarting=False)
