from __future__ import annotations

import asyncio
import contextlib
import logging
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


def _agent(registry: dict[KernelId, Any]) -> MagicMock:
    agent = MagicMock()
    agent.kernel_registry = registry
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


@pytest.fixture
def registered_agent(kernel_id: KernelId) -> MagicMock:
    return _agent({kernel_id: MagicMock()})


@pytest.fixture
def empty_agent() -> MagicMock:
    return _agent({})


class TestCreateKernelDuplicate:
    async def test_registered_kernel_is_rejected_before_any_setup(
        self, kernel_id: KernelId, registered_agent: MagicMock
    ) -> None:
        with pytest.raises(KernelAlreadyExistsError):
            await _create_kernel(registered_agent, kernel_id, restarting=False)

        registered_agent.anycast_and_broadcast_event.assert_not_awaited()
        registered_agent.init_kernel_context.assert_not_awaited()

    async def test_restart_of_a_registered_kernel_proceeds(
        self, kernel_id: KernelId, registered_agent: MagicMock
    ) -> None:
        with pytest.raises(_InitAborted):
            await _create_kernel(registered_agent, kernel_id, restarting=True)

        registered_agent.init_kernel_context.assert_awaited_once()

    async def test_unregistered_kernel_proceeds(
        self, kernel_id: KernelId, empty_agent: MagicMock
    ) -> None:
        with pytest.raises(_InitAborted):
            await _create_kernel(empty_agent, kernel_id, restarting=False)

        empty_agent.init_kernel_context.assert_awaited_once()


class _DuplicateRPC:
    agent: MagicMock
    server: MagicMock

    def __init__(self, kernel_id: KernelId) -> None:
        self.agent = MagicMock()
        self.agent.id = AgentId("i-test")
        self.agent.kernel_creation_sema = asyncio.Semaphore(1)
        self.agent.create_kernel = AsyncMock(side_effect=KernelAlreadyExistsError)
        self.agent.produce_error_event = AsyncMock()
        self.agent.inject_container_lifecycle_event = AsyncMock()
        self.server = MagicMock()
        self.server.runtime.get_agent.return_value = self.agent
        self.server.error_monitor.capture_exception = AsyncMock()
        image_ref = MagicMock()
        image_ref.canonical = "cr.backend.ai/stable/python:latest"
        self.request = RPCMessage(
            None,
            RPCMessageTypes.FUNCTION,
            "create_kernels",
            "",
            0,
            None,
            {
                "args": (str(uuid.uuid4()), [str(kernel_id)], [{}], {}, {kernel_id: image_ref}),
                "kwargs": {},
            },
        )

    async def call(self) -> Any:
        return await AgentRPCServer.create_kernels(cast(AgentRPCServer, self.server), self.request)


@pytest.fixture
def duplicate_rpc(kernel_id: KernelId) -> _DuplicateRPC:
    return _DuplicateRPC(kernel_id)


class TestCreateKernelsDuplicate:
    async def test_rejection_is_an_expected_outcome(
        self, duplicate_rpc: _DuplicateRPC, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.DEBUG), pytest.raises(KernelAlreadyExistsError):
            await duplicate_rpc.call()

        assert not [r for r in caplog.records if r.levelno >= logging.ERROR]
        duplicate_rpc.server.error_monitor.capture_exception.assert_not_awaited()
        duplicate_rpc.agent.produce_error_event.assert_awaited_once()

    async def test_rejection_does_not_inject_a_lifecycle_event(
        self, duplicate_rpc: _DuplicateRPC
    ) -> None:
        with pytest.raises(KernelAlreadyExistsError):
            await duplicate_rpc.call()

        duplicate_rpc.agent.inject_container_lifecycle_event.assert_not_awaited()
