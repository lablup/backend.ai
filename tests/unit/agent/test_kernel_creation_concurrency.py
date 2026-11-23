from __future__ import annotations

import functools
import uuid
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import aiotools
import pytest
from callosum.rpc import RPCMessage
from callosum.rpc.message import RPCMessageTypes

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.errors.resources import KernelCreationInProgress, ResourceError
from ai.backend.agent.server import AgentRPCServer
from ai.backend.common.types import AgentId, KernelId, SessionId


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

    async def test_a_create_for_a_kernel_being_created_raises_creation_in_progress(
        self, agent: MagicMock, kernel_id: KernelId
    ) -> None:
        with agent.track_create(kernel_id, SessionId(uuid.uuid4())):
            with pytest.raises(KernelCreationInProgress):
                await self._create(agent, kernel_id, restarting=False)

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


def _server_rejecting_with(*errors: Exception) -> AgentRPCServer:
    agent = MagicMock()
    agent.id = AgentId("i-test")
    agent.local_config.agent.kernel_creation_concurrency = len(errors)
    agent.create_kernel = AsyncMock(side_effect=list(errors))
    agent.produce_error_event = AsyncMock()
    server = MagicMock()
    server.runtime.get_agent.return_value = agent
    server.error_monitor.capture_exception = AsyncMock()
    return cast(AgentRPCServer, server)


async def _create_kernels(server: AgentRPCServer, num_kernels: int) -> Any:
    kernel_ids = [uuid.uuid4() for _ in range(num_kernels)]
    args: tuple[Any, ...] = (
        str(uuid.uuid4()),
        [str(k) for k in kernel_ids],
        [{"image": {"canonical": "cr.backend.ai/stable/python:latest"}} for _ in kernel_ids],
        {},
        dict.fromkeys(kernel_ids, MagicMock()),
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


class TestCreateKernelsErrors:
    async def test_kernels_all_being_created_answer_with_one_creation_in_progress(
        self,
    ) -> None:
        server = _server_rejecting_with(
            KernelCreationInProgress("Kernel creation already in progress"),
            KernelCreationInProgress("Kernel creation already in progress"),
        )

        with pytest.raises(KernelCreationInProgress):
            await _create_kernels(server, 2)

    async def test_a_creation_in_progress_mixed_with_another_failure_is_a_task_group_error(
        self,
    ) -> None:
        server = _server_rejecting_with(
            KernelCreationInProgress("Kernel creation already in progress"),
            ResourceError("Kernel already created"),
        )

        with pytest.raises(aiotools.TaskGroupError):
            await _create_kernels(server, 2)
