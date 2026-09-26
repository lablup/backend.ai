"""
Tests for agent configuration and RPC server functionality.
"""

from __future__ import annotations

import inspect
import os
from typing import Any
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
from ai.backend.agent.types import AgentBackend
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
    """The manager sends the session's `status_info` as the termination reason, and that column is
    free text -- production rows hold `rig-cleanup`, `All kernels cancelled`, `UNKNOWN`. It is
    annotated as `KernelLifecycleEventReason` but crosses RPC as a plain string, and
    `_handle_clean_event` feeds it to a pydantic event that refuses anything off the enum. The
    ValidationError killed the lifecycle task before it could send
    `KernelTerminatedAnycastEvent`, so the container was gone and the manager was never told.
    """

    @pytest.mark.parametrize(
        "sent",
        ["UNKNOWN", "rig-cleanup", "All kernels cancelled", "", "self_terminated"],
        ids=["uppercase", "free-text", "sentence", "empty", "wrong-separator"],
    )
    def test_an_unrecognised_reason_becomes_the_enums_own_unknown(self, sent: str) -> None:
        coerced = KernelLifecycleEventReason.from_value(sent) or KernelLifecycleEventReason.UNKNOWN
        assert isinstance(coerced, KernelLifecycleEventReason)
        KernelTerminatedAnycastEvent(
            kernel_id=KernelId(uuid4()),
            session_id=SessionId(uuid4()),
            reason=coerced,
        )

    @pytest.mark.parametrize(
        "sent",
        ["user-requested", "self-terminated", "already-terminated", "force-terminated"],
    )
    def test_a_reason_the_enum_knows_is_passed_through_unchanged(self, sent: str) -> None:
        coerced = KernelLifecycleEventReason.from_value(sent) or KernelLifecycleEventReason.UNKNOWN
        assert coerced.value == sent, "a valid reason must not be flattened to UNKNOWN"

    def test_the_agent_coerces_at_the_one_funnel_every_event_passes_through(self) -> None:
        """Guards the placement, not just the helper: the coercion has to sit in
        `inject_container_lifecycle_event`, which is what both the RPC entry points and the
        agent's own internal callers go through."""
        source = inspect.getsource(AbstractAgent.inject_container_lifecycle_event)
        assert "KernelLifecycleEventReason.from_value(reason)" in source, (
            "the reason is no longer coerced where every lifecycle event enters"
        )
