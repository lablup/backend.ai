"""
Tests for agent configuration and RPC server functionality.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable
from unittest.mock import AsyncMock, Mock, patch

import pytest
import tomlkit

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.config.unified import (
    AgentBackend,
    AgentConfig,
    AgentUnifiedConfig,
    ContainerConfig,
    EtcdConfig,
    ResourceConfig,
    ScratchType,
)
from ai.backend.agent.dummy.agent import DummyAgent
from ai.backend.agent.server import AgentRPCServer
from ai.backend.common.typed_validators import HostPortPair
from ai.backend.common.types import AgentId


@pytest.fixture
def mock_etcd() -> Mock:
    """Create a mock etcd object with get_prefix method."""
    etcd = Mock()
    etcd.get_prefix = None
    return etcd


@pytest.fixture
def base_agent_config() -> AgentUnifiedConfig:
    """Create a base agent configuration for testing."""
    return AgentUnifiedConfig(
        agent=AgentConfig(backend=AgentBackend.DOCKER),
        container=ContainerConfig(scratch_type=ScratchType.HOSTDIR),
        resource=ResourceConfig(),
        etcd=EtcdConfig(namespace="test", addr=HostPortPair(host="127.0.0.1", port=2379)),
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


@pytest.fixture
def mock_agent_factory() -> Callable[[str, str], Mock]:
    """Factory fixture to create mock agent instances with specified agent_id."""

    def _create_agent(agent_id: str, scaling_group: str = "default") -> Mock:
        mock_agent = Mock(spec=DummyAgent)
        mock_agent.id = AgentId(agent_id)
        mock_agent.local_config = AgentUnifiedConfig(
            agent=AgentConfig(backend=AgentBackend.DUMMY, scaling_group=scaling_group, id=agent_id),
            container=ContainerConfig(scratch_type=ScratchType.HOSTDIR),
            resource=ResourceConfig(),
            etcd=EtcdConfig(namespace="test", addr=HostPortPair(host="127.0.0.1", port=2379)),
        )

        # Use the real update_scaling_group method - capture agent in closure properly
        def update_sg(sg: str) -> None:
            AbstractAgent.update_scaling_group(mock_agent, sg)

        mock_agent.update_scaling_group = update_sg
        return mock_agent

    return _create_agent


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
    @pytest.mark.asyncio
    async def test_read_agent_config_container(
        self,
        agent_rpc_server: AgentRPCServer,
        mocker,
        etcd_response: dict,
        expected_gid: int,
        expected_uid: int,
    ) -> None:
        """Test reading container config from etcd with various responses."""
        inspect_mock = AsyncMock(return_value=etcd_response)
        mocker.patch.object(agent_rpc_server.etcd, "get_prefix", new=inspect_mock)

        await agent_rpc_server.read_agent_config_container()

        assert agent_rpc_server.local_config.container.kernel_gid.real == expected_gid
        assert agent_rpc_server.local_config.container.kernel_uid.real == expected_uid


class TestScalingGroupUpdates:
    """Tests for updating scaling group configuration."""

    def test_update_scaling_group_changes_config(self) -> None:
        """Test that update_scaling_group modifies the in-memory config."""
        mock_agent = Mock(spec=DummyAgent)
        mock_agent.local_config = AgentUnifiedConfig(
            agent=AgentConfig(backend=AgentBackend.DUMMY, scaling_group="default"),
            container=ContainerConfig(scratch_type=ScratchType.HOSTDIR),
            resource=ResourceConfig(),
            etcd=EtcdConfig(namespace="test", addr=HostPortPair(host="127.0.0.1", port=2379)),
        )

        AbstractAgent.update_scaling_group(mock_agent, "gpu")

        assert mock_agent.local_config.agent.scaling_group == "gpu"

    @pytest.mark.asyncio
    async def test_update_scaling_group_persists_single_agent(
        self, tmp_path: Path, mock_agent_factory: Callable[[str, str], Mock]
    ) -> None:
        """Test that scaling group updates persist to config file in single-agent mode."""
        config_file = tmp_path / "agent.toml"
        config_file.write_text(
            """[agent]
backend = "dummy"
scaling-group = "default"
id = "test-agent"

[container]
scratch-type = "hostdir"

[resource]

[etcd]
namespace = "test"
addr = { host = "127.0.0.1", port = 2379 }
"""
        )

        # Create server with runtime
        server = object.__new__(AgentRPCServer)
        runtime = Mock()
        runtime._default_agent_id = AgentId("test-agent")

        def get_agent_impl(agent_id=None):
            if agent_id is None:
                agent_id = runtime._default_agent_id
            return runtime.agents[agent_id]

        runtime.get_agent = get_agent_impl

        mock_agent = mock_agent_factory("test-agent", "default")
        runtime.agents = {AgentId("test-agent"): mock_agent}
        server.runtime = runtime

        with patch("ai.backend.common.config.find_config_file", return_value=config_file):
            await server.update_scaling_group.__wrapped__.__wrapped__(server, "gpu", None)  # type: ignore[attr-defined]

        # Verify file was updated
        with open(config_file) as f:
            updated_config = tomlkit.load(f)

        assert updated_config["agent"]["scaling-group"] == "gpu"  # type: ignore[index]
        assert mock_agent.local_config.agent.scaling_group == "gpu"

    @pytest.mark.asyncio
    async def test_update_scaling_group_persists_multi_agent(
        self, tmp_path: Path, mock_agent_factory: Callable[[str, str], Mock]
    ) -> None:
        """Test that scaling group updates persist correctly in multi-agent mode."""
        config_file = tmp_path / "agent.toml"
        config_file.write_text(
            """[agent]
backend = "dummy"
scaling-group = "default"

[container]
scratch-type = "hostdir"

[resource]

[etcd]
namespace = "test"
addr = { host = "127.0.0.1", port = 2379 }

[[agents]]
[agents.agent]
id = "agent-1"
scaling-group = "default"

[[agents]]
[agents.agent]
id = "agent-2"
scaling-group = "default"
"""
        )

        # Create server with runtime
        server = object.__new__(AgentRPCServer)
        runtime = Mock()
        runtime._default_agent_id = AgentId("agent-1")

        def get_agent_impl(agent_id=None):
            if agent_id is None:
                agent_id = runtime._default_agent_id
            return runtime.agents[agent_id]

        runtime.get_agent = get_agent_impl

        mock_agent1 = mock_agent_factory("agent-1", "default")
        mock_agent2 = mock_agent_factory("agent-2", "default")

        runtime.agents = {
            AgentId("agent-1"): mock_agent1,
            AgentId("agent-2"): mock_agent2,
        }
        server.runtime = runtime

        with patch("ai.backend.common.config.find_config_file", return_value=config_file):
            await server.update_scaling_group.__wrapped__.__wrapped__(  # type: ignore[attr-defined]
                server, "gpu", AgentId("agent-2")
            )  # type: ignore[attr-defined]

        # Verify file was updated
        with open(config_file) as f:
            updated_config = tomlkit.load(f)

        # Only agent-2's scaling group should be updated
        assert updated_config["agents"][1]["agent"]["scaling-group"] == "gpu"  # type: ignore[index]
        assert updated_config["agents"][0]["agent"]["scaling-group"] == "default"  # type: ignore[index]
        assert mock_agent2.local_config.agent.scaling_group == "gpu"
        assert mock_agent1.local_config.agent.scaling_group == "default"
