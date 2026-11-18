from __future__ import annotations

import functools
import uuid
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.errors.resources import ResourceError
from ai.backend.common.types import KernelId, SessionId


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
