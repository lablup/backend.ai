"""How the agent judges a registered kernel that the container listing does not have."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Sequence
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.types import KernelLifecycleStatus
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import AgentId, KernelId, SessionId


@dataclass(frozen=True)
class _KernelAbsentFromListingCase:
    """A kernel that is RUNNING in the registry once the listing without it returns."""

    description: str
    state_before_listing: KernelLifecycleStatus
    restarted_during_listing: bool = False
    expected_event_reasons: Sequence[KernelLifecycleEventReason] = field(default_factory=list)
    expected_registered: bool = True


@dataclass(frozen=True)
class _KernelAbsentFromListing:
    agent: Any
    kernel_id: KernelId


class TestKernelAbsentFromContainerListing:
    def _kernel(self, state: KernelLifecycleStatus) -> MagicMock:
        kernel_obj = MagicMock()
        kernel_obj.session_id = SessionId(uuid4())
        kernel_obj.state = state
        kernel_obj.container_id = "container-1"
        kernel_obj.runner = None
        kernel_obj.close = AsyncMock()
        kernel_obj.get.return_value = None
        return kernel_obj

    @pytest.fixture
    def kernel_absent_from_listing(
        self, case: _KernelAbsentFromListingCase
    ) -> _KernelAbsentFromListing:
        kernel_id = KernelId(uuid4())
        kernel_before_listing = self._kernel(case.state_before_listing)
        kernel_after_listing = (
            self._kernel(KernelLifecycleStatus.RUNNING)
            if case.restarted_during_listing
            else kernel_before_listing
        )
        kernel_registry = {kernel_id: kernel_before_listing}

        async def _list_no_container(*args: Any) -> list[Any]:
            kernel_after_listing.state = KernelLifecycleStatus.RUNNING
            kernel_registry[kernel_id] = kernel_after_listing
            return []

        agent = SimpleNamespace(
            id=AgentId("test-agent"),
            enumerate_containers=_list_no_container,
            registry_lock=asyncio.Lock(),
            restarting_kernels={},
            kernel_registry=kernel_registry,
            container_lifecycle_queue=asyncio.Queue(),
            set_container_count=AsyncMock(),
            produce_error_event=AsyncMock(),
            _sync_container_lifecycle_observer=MagicMock(),
        )
        for name in ("clean_kernel_objects", "_clean_kernel_object"):
            setattr(agent, name, functools.partial(getattr(AbstractAgent, name), cast(Any, agent)))
        return _KernelAbsentFromListing(agent=agent, kernel_id=kernel_id)

    @pytest.mark.parametrize(
        "case",
        [
            _KernelAbsentFromListingCase(
                description="started during the listing",
                state_before_listing=KernelLifecycleStatus.PREPARING,
            ),
            _KernelAbsentFromListingCase(
                description="restarted during the listing",
                state_before_listing=KernelLifecycleStatus.RUNNING,
                restarted_during_listing=True,
            ),
            _KernelAbsentFromListingCase(
                description="running since before the listing",
                state_before_listing=KernelLifecycleStatus.RUNNING,
                expected_event_reasons=[KernelLifecycleEventReason.CONTAINER_NOT_FOUND],
            ),
        ],
        ids=lambda case: case.description,
    )
    async def test_lifecycle_sync_cleans_only_a_kernel_running_since_before_the_listing(
        self,
        case: _KernelAbsentFromListingCase,
        kernel_absent_from_listing: _KernelAbsentFromListing,
    ) -> None:
        agent = kernel_absent_from_listing.agent

        await AbstractAgent.sync_container_lifecycles(agent)

        agent.produce_error_event.assert_not_called()
        event_reasons = [
            agent.container_lifecycle_queue.get_nowait().reason
            for _ in range(agent.container_lifecycle_queue.qsize())
        ]
        assert event_reasons == case.expected_event_reasons

    @pytest.mark.parametrize(
        "case",
        [
            _KernelAbsentFromListingCase(
                description="started during the listing",
                state_before_listing=KernelLifecycleStatus.PREPARING,
            ),
            _KernelAbsentFromListingCase(
                description="restarted during the listing",
                state_before_listing=KernelLifecycleStatus.RUNNING,
                restarted_during_listing=True,
            ),
            _KernelAbsentFromListingCase(
                description="running since before the listing",
                state_before_listing=KernelLifecycleStatus.RUNNING,
                expected_registered=False,
            ),
        ],
        ids=lambda case: case.description,
    )
    async def test_registry_cleanup_drops_only_a_kernel_running_since_before_the_listing(
        self,
        case: _KernelAbsentFromListingCase,
        kernel_absent_from_listing: _KernelAbsentFromListing,
    ) -> None:
        agent = kernel_absent_from_listing.agent

        cleanup_loop = asyncio.create_task(AbstractAgent._clean_kernel_registry_loop(agent))
        for _ in range(10):
            await asyncio.sleep(0)
        cleanup_loop.cancel()
        await asyncio.gather(cleanup_loop, return_exceptions=True)

        registered = kernel_absent_from_listing.kernel_id in agent.kernel_registry
        assert registered is case.expected_registered
