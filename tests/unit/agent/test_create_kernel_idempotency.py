"""
Tests for create_kernel idempotency (BA-6646).

The manager re-sends ``create_kernels`` for sessions stuck in CREATING, so
``AbstractAgent.create_kernel`` must not raise nor create a duplicate
container when called again for the same kernel:

- already-running kernel  -> re-emit KernelStarted events and return the
  reconstructed creation info
- kernel in the registry but not RUNNING yet -> skip (return None)
- creation in flight (tracked by ``_active_creates``) -> skip (return None)
"""

from __future__ import annotations

import uuid
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.resources import KernelResourceSpec
from ai.backend.agent.types import KernelLifecycleStatus, KernelOwnershipData
from ai.backend.common.events.event_types.kernel.anycast import KernelStartedAnycastEvent
from ai.backend.common.events.event_types.kernel.broadcast import KernelStartedBroadcastEvent
from ai.backend.common.types import (
    AgentId,
    ClusterInfo,
    KernelCreationConfig,
    KernelId,
    ResourceSlot,
    SessionId,
)

KERNEL_ID = KernelId(uuid.uuid4())
SESSION_ID = SessionId(uuid.uuid4())
AGENT_ID = AgentId("i-test")
CONTAINER_ID = "c-0123456789abcdef"


@pytest.fixture
def ownership_data() -> KernelOwnershipData:
    return KernelOwnershipData(KERNEL_ID, SESSION_ID, AGENT_ID)


@pytest.fixture
def kernel_config() -> KernelCreationConfig:
    return cast(
        KernelCreationConfig,
        {
            "scaling_group": "default",
            "agent_addr": "tcp://127.0.0.1:6011",
        },
    )


@pytest.fixture
def running_kernel_obj() -> MagicMock:
    kernel_obj = MagicMock(spec=AbstractKernel)
    kernel_obj.state = KernelLifecycleStatus.RUNNING
    kernel_obj.kernel_id = KERNEL_ID
    kernel_obj.session_id = SESSION_ID
    kernel_obj.resource_spec = KernelResourceSpec(
        slots=ResourceSlot(),
        allocations={},
        scratch_disk_size=0,
    )
    kernel_obj.service_ports = []
    data = {
        "kernel_host": "127.0.0.1",
        "repl_in_port": 2000,
        "repl_out_port": 2001,
        "stdin_port": 2002,
        "stdout_port": 2003,
        "container_id": CONTAINER_ID,
    }
    kernel_obj.__getitem__.side_effect = data.__getitem__
    return kernel_obj


@pytest.fixture
def stub_agent() -> Mock:
    """A stub standing in for an AbstractAgent instance.

    The real ``create_kernel`` / ``track_create`` / ``_replay_kernel_started_event``
    implementations are exercised unbound against this stub.
    """
    agent = Mock(spec=AbstractAgent)
    agent._active_creates = {}
    agent.kernel_registry = {}
    agent.computers = {}
    agent.get_public_service_ports = Mock(side_effect=lambda service_ports: service_ports)
    agent.anycast_and_broadcast_event = AsyncMock()
    agent.track_create = lambda kernel_id, session_id: AbstractAgent.track_create(
        agent, kernel_id, session_id
    )
    agent._replay_kernel_started_event = (
        lambda kernel_obj, kernel_config: AbstractAgent._replay_kernel_started_event(
            agent, kernel_obj, kernel_config
        )
    )
    return agent


async def _call_create_kernel(
    stub_agent: Mock,
    ownership_data: KernelOwnershipData,
    kernel_config: KernelCreationConfig,
) -> Any:
    return await AbstractAgent.create_kernel(
        stub_agent,
        ownership_data,
        MagicMock(),  # kernel_image
        kernel_config,
        cast(ClusterInfo, {}),
    )


class TestCreateKernelIdempotency:
    async def test_running_kernel_reemits_started_events(
        self,
        stub_agent: Mock,
        running_kernel_obj: MagicMock,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        """A re-sent create for an already-running kernel re-emits the
        KernelStarted events (recovering a lost event) and returns the
        reconstructed creation info without creating a new container."""
        stub_agent.kernel_registry[KERNEL_ID] = running_kernel_obj

        result = await _call_create_kernel(stub_agent, ownership_data, kernel_config)

        assert result is not None
        assert result["id"] == KERNEL_ID
        assert result["container_id"] == CONTAINER_ID
        assert result["kernel_host"] == "127.0.0.1"
        assert result["scaling_group"] == "default"
        assert result["agent_addr"] == "tcp://127.0.0.1:6011"

        stub_agent.anycast_and_broadcast_event.assert_awaited_once()
        anycast_event, broadcast_event = stub_agent.anycast_and_broadcast_event.await_args.args
        assert isinstance(anycast_event, KernelStartedAnycastEvent)
        assert isinstance(broadcast_event, KernelStartedBroadcastEvent)
        assert anycast_event.kernel_id == KERNEL_ID
        assert anycast_event.session_id == SESSION_ID
        assert anycast_event.creation_info["id"] == str(KERNEL_ID)
        assert anycast_event.creation_info["container_id"] == CONTAINER_ID

        # No creation was tracked; the call short-circuited.
        assert KERNEL_ID not in stub_agent._active_creates

    async def test_registered_but_not_running_kernel_is_skipped(
        self,
        stub_agent: Mock,
        running_kernel_obj: MagicMock,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        """A kernel present in the registry but not RUNNING yet must not be
        re-created nor have its events replayed."""
        running_kernel_obj.state = KernelLifecycleStatus.PREPARING
        stub_agent.kernel_registry[KERNEL_ID] = running_kernel_obj

        result = await _call_create_kernel(stub_agent, ownership_data, kernel_config)

        assert result is None
        stub_agent.anycast_and_broadcast_event.assert_not_awaited()

    async def test_inflight_creation_is_skipped_without_raising(
        self,
        stub_agent: Mock,
        ownership_data: KernelOwnershipData,
        kernel_config: KernelCreationConfig,
    ) -> None:
        """A re-sent create while another creation is in flight returns None
        instead of raising, so the manager's periodic re-send is harmless."""
        stub_agent._active_creates[KERNEL_ID] = Mock()

        result = await _call_create_kernel(stub_agent, ownership_data, kernel_config)

        assert result is None
        stub_agent.anycast_and_broadcast_event.assert_not_awaited()
        # The in-flight tracking entry must be left intact.
        assert KERNEL_ID in stub_agent._active_creates
