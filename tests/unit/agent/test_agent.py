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
from ai.backend.common.configs.etcd import EtcdConfig, EtcdTLSConfig
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
            keep_alive_interval=5.0,
            keep_alive_timeout=3.0,
            tls=EtcdTLSConfig(
                enabled=False,
                ca_cert=None,
                client_cert=None,
                client_key=None,
                handshake_timeout=None,
            ),
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


class TestCleanEventOfAKernelBeingDestroyed:
    """DESTROY hands its done future to the kernel as `clean_event`, and CLEAN gets the same one."""

    @pytest.fixture
    def kernel_id(self) -> KernelId:
        return KernelId(uuid4())

    @pytest.fixture
    async def clean_event(self) -> asyncio.Future[Any]:
        return asyncio.get_running_loop().create_future()

    @pytest.fixture
    def agent(self, kernel_id: KernelId, clean_event: asyncio.Future[Any]) -> SimpleNamespace:
        kernel_obj = Mock(runner=None, clean_event=clean_event, close=AsyncMock())
        kernel_obj.get.return_value = None
        return SimpleNamespace(
            _ongoing_destruction_tasks={},
            stat_ctx=SimpleNamespace(remove_kernel_metric=AsyncMock()),
            registry_lock=asyncio.Lock(),
            kernel_registry={kernel_id: kernel_obj},
            restarting_kernels={},
            clean_kernel=AsyncMock(),
            reconstruct_resource_usage=AsyncMock(),
            anycast_and_broadcast_event=AsyncMock(),
            produce_error_event=AsyncMock(),
        )

    @pytest.fixture
    def clean(
        self, kernel_id: KernelId, clean_event: asyncio.Future[Any]
    ) -> ContainerLifecycleEvent:
        return ContainerLifecycleEvent(
            kernel_id,
            SessionId(uuid4()),
            None,
            LifecycleEvent.CLEAN,
            KernelLifecycleEventReason.USER_REQUESTED,
            done_future=clean_event,
        )

    async def test_a_failed_clean_leaves_its_exception_to_the_waiter(
        self,
        agent: SimpleNamespace,
        clean: ContainerLifecycleEvent,
        clean_event: asyncio.Future[Any],
    ) -> None:
        error = RuntimeError("scratch removal failed")
        agent.clean_kernel.side_effect = error

        await AbstractAgent._handle_clean_event(cast(Any, agent), clean)

        assert clean_event.exception() is error
        agent.anycast_and_broadcast_event.assert_awaited_once()

    async def test_a_clean_that_succeeds_ends_the_waiter_with_none(
        self,
        agent: SimpleNamespace,
        clean: ContainerLifecycleEvent,
        clean_event: asyncio.Future[Any],
    ) -> None:
        await AbstractAgent._handle_clean_event(cast(Any, agent), clean)

        assert clean_event.result() is None
