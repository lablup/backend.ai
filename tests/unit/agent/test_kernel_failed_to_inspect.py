"""A kernel whose container failed to be inspected is not taken as a kernel without one."""

from __future__ import annotations

import asyncio
import functools
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.types import ContainerListing, KernelLifecycleStatus
from ai.backend.common.types import AgentId, KernelId, SessionId


@dataclass(frozen=True)
class _RunningKernelFailedToInspect:
    agent: Any
    kernel_id: KernelId


class TestRunningKernelFailedToInspect:
    @pytest.fixture
    def running_kernel_failed_to_inspect(self) -> _RunningKernelFailedToInspect:
        kernel_id = KernelId(uuid4())
        kernel_obj = MagicMock()
        kernel_obj.session_id = SessionId(uuid4())
        kernel_obj.state = KernelLifecycleStatus.RUNNING
        kernel_obj.container_id = "container-1"
        kernel_obj.runner = None
        kernel_obj.close = AsyncMock()
        kernel_obj.get.return_value = None
        agent = SimpleNamespace(
            id=AgentId("test-agent"),
            enumerate_containers=AsyncMock(
                return_value=ContainerListing(
                    containers=[], kernel_ids_failed_to_inspect=frozenset({kernel_id})
                )
            ),
            registry_lock=asyncio.Lock(),
            restarting_kernels={},
            kernel_registry={kernel_id: kernel_obj},
            container_lifecycle_queue=asyncio.Queue(),
            set_container_count=AsyncMock(),
            produce_error_event=AsyncMock(),
            _sync_container_lifecycle_observer=MagicMock(),
        )
        for name in ("clean_kernel_objects", "_clean_kernel_object"):
            setattr(agent, name, functools.partial(getattr(AbstractAgent, name), cast(Any, agent)))
        return _RunningKernelFailedToInspect(agent=agent, kernel_id=kernel_id)

    async def test_lifecycle_sync_does_not_clean_it(
        self, running_kernel_failed_to_inspect: _RunningKernelFailedToInspect
    ) -> None:
        agent = running_kernel_failed_to_inspect.agent

        await AbstractAgent.sync_container_lifecycles(agent)

        agent.produce_error_event.assert_not_called()
        assert agent.container_lifecycle_queue.empty()

    async def test_registry_cleanup_does_not_drop_it(
        self, running_kernel_failed_to_inspect: _RunningKernelFailedToInspect
    ) -> None:
        agent = running_kernel_failed_to_inspect.agent

        cleanup_loop = asyncio.create_task(AbstractAgent._clean_kernel_registry_loop(agent))
        for _ in range(10):
            await asyncio.sleep(0)
        cleanup_loop.cancel()
        await asyncio.gather(cleanup_loop, return_exceptions=True)

        assert running_kernel_failed_to_inspect.kernel_id in agent.kernel_registry
