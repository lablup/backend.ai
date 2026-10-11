"""
Tests for agent configuration and RPC server functionality.
"""

from __future__ import annotations

import asyncio
import os
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.config.unified import (
    AgentConfig,
    AgentUnifiedConfig,
    ContainerConfig,
    ResourceConfig,
    ScratchType,
)
from ai.backend.agent.server import AgentRPCServer
from ai.backend.agent.types import AgentBackend, ContainerLifecycleEvent, LifecycleEvent
from ai.backend.common.configs.etcd import EtcdConfig
from ai.backend.common.events.event_types.kernel.anycast import KernelTerminatedAnycastEvent
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.typed_validators import HostPortPair
from ai.backend.common.types import KernelId, SessionId


@pytest.fixture
def mock_etcd() -> Mock:
    """Create a mock etcd object with get_prefix method."""
    etcd = Mock()
    etcd.get_prefix = None
    return etcd


@pytest.fixture
def base_agent_config() -> AgentUnifiedConfig:
    """Create a base agent configuration for testing."""
    return AgentUnifiedConfig(  # type: ignore[call-arg]
        agent=AgentConfig(backend=AgentBackend.DOCKER),  # type: ignore[call-arg]
        container=ContainerConfig(scratch_type=ScratchType.HOSTDIR),  # type: ignore[call-arg]
        resource=ResourceConfig(),  # type: ignore[call-arg]
        etcd=EtcdConfig(
            namespace="test",
            addr=HostPortPair(host="127.0.0.1", port=2379),
            user=None,
            password=None,
        ),
    )


@pytest.fixture
async def agent_rpc_server(
    mock_etcd: Mock, base_agent_config: AgentUnifiedConfig
) -> AgentRPCServer:
    """Create an AgentRPCServer instance for testing without initialization."""
    ars = AgentRPCServer(etcd=mock_etcd, local_config=base_agent_config, skip_detect_manager=True)

    # Mock the runtime object to return the etcd client
    runtime = Mock()
    runtime.get_etcd = lambda agent_id=None: mock_etcd
    ars.runtime = runtime

    return ars


class TestAgentConfigReading:
    """Tests for reading agent configuration from etcd."""

    @pytest.mark.parametrize(
        "etcd_response,expected_gid,expected_uid",
        [
            # Invalid responses - should use defaults
            ({"a": 1, "b": 2}, os.getgid(), os.getuid()),
            ({}, os.getgid(), os.getuid()),
            # Partial valid responses
            ({"kernel-gid": 10}, 10, os.getuid()),
            # Fully valid response
            ({"kernel-gid": 10, "kernel-uid": 20}, 10, 20),
        ],
        ids=["invalid_keys", "empty", "only_gid", "both_valid"],
    )
    async def test_read_agent_config_container(
        self,
        agent_rpc_server: AgentRPCServer,
        mocker: Any,
        etcd_response: dict[str, Any],
        expected_gid: int,
        expected_uid: int,
    ) -> None:
        """Test reading container config from etcd with various responses."""
        inspect_mock = AsyncMock(return_value=etcd_response)
        mocker.patch.object(agent_rpc_server.etcd, "get_prefix", new=inspect_mock)

        await agent_rpc_server.read_agent_config_container()

        assert agent_rpc_server.local_config.container.kernel_gid.real == expected_gid
        assert agent_rpc_server.local_config.container.kernel_uid.real == expected_uid


class TestALifecycleReasonNeverBreaksTheCleanHandler:
    """The manager sends free-text `status_info` as the reason; anything off the enum must reach
    the lifecycle queue as UNKNOWN, or the terminated event is never sent."""

    @staticmethod
    async def _queued_reason(sent: str) -> KernelLifecycleEventReason:
        agent = SimpleNamespace(kernel_registry={}, container_lifecycle_queue=asyncio.Queue())
        await AbstractAgent.inject_container_lifecycle_event(
            cast(Any, agent),
            KernelId(uuid4()),
            SessionId(uuid4()),
            LifecycleEvent.CLEAN,
            cast(KernelLifecycleEventReason, sent),
        )
        queued: ContainerLifecycleEvent = agent.container_lifecycle_queue.get_nowait()
        return queued.reason

    @pytest.mark.parametrize(
        "sent",
        ["UNKNOWN", "rig-cleanup", "All kernels cancelled", "", "self_terminated"],
        ids=["uppercase", "free-text", "sentence", "empty", "wrong-separator"],
    )
    async def test_an_unrecognised_reason_becomes_unknown(self, sent: str) -> None:
        reason = await self._queued_reason(sent)
        assert reason is KernelLifecycleEventReason.UNKNOWN
        KernelTerminatedAnycastEvent(
            kernel_id=KernelId(uuid4()), session_id=SessionId(uuid4()), reason=reason
        )

    @pytest.mark.parametrize(
        "sent",
        ["user-requested", "self-terminated", "already-terminated", "force-terminated"],
    )
    async def test_a_reason_the_enum_knows_is_passed_through_unchanged(self, sent: str) -> None:
        assert (await self._queued_reason(sent)).value == sent

    async def test_a_free_text_termination_reason_restored_on_the_kernel_becomes_unknown(
        self,
    ) -> None:
        # An older agent's on-disk registry may restore `termination_reason` as free text.
        kernel_id = KernelId(uuid4())
        kernel_obj = Mock(termination_reason="rig-cleanup")
        kernel_obj.get.return_value = "container-1"
        agent = SimpleNamespace(
            kernel_registry={kernel_id: kernel_obj}, container_lifecycle_queue=asyncio.Queue()
        )
        await AbstractAgent.inject_container_lifecycle_event(
            cast(Any, agent),
            kernel_id,
            SessionId(uuid4()),
            LifecycleEvent.CLEAN,
            KernelLifecycleEventReason.USER_REQUESTED,
        )
        queued: ContainerLifecycleEvent = agent.container_lifecycle_queue.get_nowait()
        assert queued.reason is KernelLifecycleEventReason.UNKNOWN
