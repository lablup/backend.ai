from __future__ import annotations

import asyncio
import uuid
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.kernel_registry.exception import KernelRecoveryDataParseError
from ai.backend.common.events.event_types.kernel.anycast import KernelStartedAnycastEvent
from ai.backend.common.events.event_types.kernel.broadcast import KernelStartedBroadcastEvent
from ai.backend.common.events.event_types.kernel.types import KernelCreationInfo, UsedDevices
from ai.backend.common.types import ContainerId, KernelId, SessionId


def _kernel() -> MagicMock:
    kernel = MagicMock()
    kernel.kernel_id = KernelId(uuid.uuid4())
    kernel.session_id = SessionId(uuid.uuid4())
    return kernel


@pytest.fixture
def kernel() -> MagicMock:
    return _kernel()


@pytest.fixture
def creation_info() -> KernelCreationInfo:
    return KernelCreationInfo(
        container_id=ContainerId("c"),
        kernel_host="127.0.0.1",
        repl_in_port=2000,
        repl_out_port=2001,
        service_ports=[],
        used_devices=UsedDevices(units={}),
    )


@pytest.fixture
def agent() -> MagicMock:
    agent = MagicMock()
    agent.kernel_registry = {}
    agent._write_kernel_to_recovery = AsyncMock()
    agent.anycast_and_broadcast_event = AsyncMock()
    return agent


async def _notify(agent: MagicMock, kernel: MagicMock, creation_info: KernelCreationInfo) -> None:
    await AbstractAgent._notify_kernel_started(
        cast(AbstractAgent[Any, Any], agent), kernel, creation_info
    )


class TestNotifyKernelStarted:
    async def test_saves_only_the_started_kernel_before_the_event(
        self, agent: MagicMock, kernel: MagicMock, creation_info: KernelCreationInfo
    ) -> None:
        order: list[str] = []
        agent._write_kernel_to_recovery.side_effect = lambda _: order.append("save")
        agent.anycast_and_broadcast_event.side_effect = lambda *_: order.append("event")

        await _notify(agent, kernel, creation_info)

        agent._write_kernel_to_recovery.assert_awaited_once_with(kernel)
        assert order == ["save", "event"]
        anycast, broadcast = agent.anycast_and_broadcast_event.await_args.args
        assert isinstance(anycast, KernelStartedAnycastEvent)
        assert isinstance(broadcast, KernelStartedBroadcastEvent)
        assert anycast.kernel_id == kernel.kernel_id
        assert anycast.session_id == kernel.session_id
        assert anycast.creation_info == creation_info

    async def test_sends_the_event_when_the_save_fails(
        self, agent: MagicMock, kernel: MagicMock, creation_info: KernelCreationInfo
    ) -> None:
        agent._write_kernel_to_recovery.side_effect = KernelRecoveryDataParseError()

        await _notify(agent, kernel, creation_info)

        agent.anycast_and_broadcast_event.assert_awaited_once()

    async def test_registry_changes_during_the_save_do_not_fail(
        self, agent: MagicMock, kernel: MagicMock, creation_info: KernelCreationInfo
    ) -> None:
        agent.kernel_registry[kernel.kernel_id] = kernel

        async def save_while_other_kernels_register(_: Any) -> None:
            for _ in range(3):
                other = _kernel()
                agent.kernel_registry[other.kernel_id] = other
                await asyncio.sleep(0)

        agent._write_kernel_to_recovery.side_effect = save_while_other_kernels_register

        await asyncio.gather(*(_notify(agent, kernel, creation_info) for _ in range(3)))

        assert agent.anycast_and_broadcast_event.await_count == 3
