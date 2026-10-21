from __future__ import annotations

import asyncio
import contextlib
import uuid
from collections.abc import Iterator
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from callosum.rpc import RPCMessage
from callosum.rpc.message import RPCMessageTypes

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.errors import KernelAlreadyExistsError
from ai.backend.agent.server import AgentRPCServer
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.types import AgentId, KernelId, SessionId


class _InitAborted(Exception):
    """Stops `create_kernel` right after the duplicate guard."""


@contextlib.contextmanager
def _track_create(kernel_id: KernelId, session_id: SessionId) -> Iterator[bool]:
    yield True


def _agent(kernel_id: KernelId) -> MagicMock:
    agent = MagicMock()
    agent.kernel_registry = {kernel_id: MagicMock()}
    agent.track_create = _track_create
    agent.local_config.debug.log_kernel_config = False
    agent.anycast_and_broadcast_event = AsyncMock()
    agent.init_kernel_context = AsyncMock(side_effect=_InitAborted)
    return agent


async def _create_kernel(agent: MagicMock, kernel_id: KernelId, *, restarting: bool) -> Any:
    ownership = KernelOwnershipData(
        kernel_id, SessionId(uuid.uuid4()), AgentId("i-test"), None, None
    )
    return await AbstractAgent.create_kernel(
        cast(AbstractAgent[Any, Any], agent),
        ownership,
        MagicMock(),
        cast(Any, {"environ": {}}),
        cast(Any, {}),
        restarting=restarting,
    )


@pytest.fixture
def kernel_id() -> KernelId:
    return KernelId(uuid.uuid4())


class TestCreateKernelDuplicate:
    async def test_registered_kernel_is_rejected_before_any_setup(
        self, kernel_id: KernelId
    ) -> None:
        agent = _agent(kernel_id)

        with pytest.raises(KernelAlreadyExistsError):
            await _create_kernel(agent, kernel_id, restarting=False)

        agent.anycast_and_broadcast_event.assert_not_awaited()
        agent.init_kernel_context.assert_not_awaited()

    async def test_restart_of_a_registered_kernel_proceeds(self, kernel_id: KernelId) -> None:
        agent = _agent(kernel_id)

        with pytest.raises(_InitAborted):
            await _create_kernel(agent, kernel_id, restarting=True)

        agent.init_kernel_context.assert_awaited_once()

    async def test_unregistered_kernel_proceeds(self, kernel_id: KernelId) -> None:
        agent = _agent(kernel_id)
        agent.kernel_registry = {}

        with pytest.raises(_InitAborted):
            await _create_kernel(agent, kernel_id, restarting=False)

        agent.init_kernel_context.assert_awaited_once()


class TestCreateKernelsDuplicate:
    async def test_rejection_does_not_inject_a_lifecycle_event(self, kernel_id: KernelId) -> None:
        agent = MagicMock()
        agent.id = AgentId("i-test")
        agent.kernel_creation_sema = asyncio.Semaphore(1)
        agent.create_kernel = AsyncMock(side_effect=KernelAlreadyExistsError)
        agent.produce_error_event = AsyncMock()
        agent.inject_container_lifecycle_event = AsyncMock()
        server = MagicMock()
        server.runtime.get_agent.return_value = agent
        server.error_monitor.capture_exception = AsyncMock()
        image_ref = MagicMock()
        image_ref.canonical = "cr.backend.ai/stable/python:latest"
        request = RPCMessage(
            None,
            RPCMessageTypes.FUNCTION,
            "create_kernels",
            "",
            0,
            None,
            {
                "args": (
                    str(uuid.uuid4()),
                    [str(kernel_id)],
                    [{}],
                    {},
                    {kernel_id: image_ref},
                ),
                "kwargs": {},
            },
        )

        with pytest.raises(KernelAlreadyExistsError):
            await AgentRPCServer.create_kernels(cast(AgentRPCServer, server), request)

        agent.inject_container_lifecycle_event.assert_not_awaited()
