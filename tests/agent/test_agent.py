"""
TODO: rewrite
"""

import os
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


class Dummy:
    def prefill_clients(self, prefill_data):
        """Mock implementation of prefill_clients for testing"""
        pass


kgid = "kernel-gid"
kuid = "kernel-uid"
ctnr = "container"


@pytest.fixture
async def arpcs_no_ainit(test_id, redis_container):
    etcd_client_registry = Dummy()
    etcd_client_registry.global_etcd = Dummy()
    etcd_client_registry.global_etcd.get_prefix = None

    # Create a minimal pydantic config for testing
    config = AgentUnifiedConfig(
        agent=AgentConfig(backend="docker"),
        container=ContainerConfig(scratch_type="hostdir"),
        resource=ResourceConfig(),
        etcd=EtcdConfig(namespace="test", addr=HostPortPair(host="127.0.0.1", port=2379)),
    )

    ars = AgentRPCServer(
        etcd_client_registry=etcd_client_registry, local_config=config, skip_detect_manager=True
    )
    yield ars


@pytest.mark.asyncio
async def test_read_agent_config_container_invalid01(arpcs_no_ainit, mocker):
    inspect_mock = AsyncMock(return_value={"a": 1, "b": 2})
    mocker.patch.object(
        arpcs_no_ainit.etcd_client_registry.global_etcd, "get_prefix", new=inspect_mock
    )
    await arpcs_no_ainit.read_agent_config_container()
    # Check that kernel-gid and kernel-uid are still at their default values (converted from -1)
    assert (
        arpcs_no_ainit.local_config.container.kernel_gid.real == os.getgid()
    )  # default value (os.getgid())
    assert (
        arpcs_no_ainit.local_config.container.kernel_uid.real == os.getuid()
    )  # default value (os.getuid())


@pytest.mark.asyncio
async def test_read_agent_config_container_invalid02(arpcs_no_ainit, mocker):
    inspect_mock = AsyncMock(return_value={})
    mocker.patch.object(
        arpcs_no_ainit.etcd_client_registry.global_etcd, "get_prefix", new=inspect_mock
    )
    await arpcs_no_ainit.read_agent_config_container()
    # Check that kernel-gid and kernel-uid are still at their default values (converted from -1)
    assert (
        arpcs_no_ainit.local_config.container.kernel_gid.real == os.getgid()
    )  # default value (os.getgid())
    assert (
        arpcs_no_ainit.local_config.container.kernel_uid.real == os.getuid()
    )  # default value (os.getuid())


@pytest.mark.asyncio
async def test_read_agent_config_container_1valid(arpcs_no_ainit, mocker):
    inspect_mock = AsyncMock(return_value={kgid: 10})
    mocker.patch.object(
        arpcs_no_ainit.etcd_client_registry.global_etcd, "get_prefix", new=inspect_mock
    )
    await arpcs_no_ainit.read_agent_config_container()

    assert arpcs_no_ainit.local_config.container.kernel_gid.real == 10
    assert (
        arpcs_no_ainit.local_config.container.kernel_uid.real == os.getuid()
    )  # default value (os.getuid())


@pytest.mark.asyncio
async def test_read_agent_config_container_2valid(arpcs_no_ainit, mocker):
    inspect_mock = AsyncMock(return_value={kgid: 10, kuid: 20})
    mocker.patch.object(
        arpcs_no_ainit.etcd_client_registry.global_etcd, "get_prefix", new=inspect_mock
    )
    await arpcs_no_ainit.read_agent_config_container()

    assert arpcs_no_ainit.local_config.container.kernel_gid.real == 10
    assert arpcs_no_ainit.local_config.container.kernel_uid.real == 20


@pytest.mark.asyncio
async def test_update_scaling_group_changes_config() -> None:
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
async def test_update_scaling_group_persists_single_agent(tmp_path) -> None:
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

    server = object.__new__(AgentRPCServer)
    server._default_agent_id = AgentId("test-agent")

    mock_agent = Mock(spec=DummyAgent)
    mock_agent.id = AgentId("test-agent")
    mock_agent.local_config = AgentUnifiedConfig(
        agent=AgentConfig(backend=AgentBackend.DUMMY, scaling_group="default", id="test-agent"),
        container=ContainerConfig(scratch_type=ScratchType.HOSTDIR),
        resource=ResourceConfig(),
        etcd=EtcdConfig(namespace="test", addr=HostPortPair(host="127.0.0.1", port=2379)),
    )
    # Use the real update_scaling_group method
    mock_agent.update_scaling_group = lambda scaling_group: AbstractAgent.update_scaling_group(
        mock_agent, scaling_group
    )
    server.agents = {AgentId("test-agent"): mock_agent}

    with patch("ai.backend.common.config.find_config_file", return_value=config_file):
        await server.update_scaling_group.__wrapped__.__wrapped__(server, "gpu", None)  # type: ignore[attr-defined]

    with open(config_file) as f:
        updated_config = tomlkit.load(f)

    assert updated_config["agent"]["scaling-group"] == "gpu"  # type: ignore[index]
    assert mock_agent.local_config.agent.scaling_group == "gpu"


@pytest.mark.asyncio
async def test_update_scaling_group_persists_multi_agent(tmp_path) -> None:
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

    server = object.__new__(AgentRPCServer)
    server._default_agent_id = AgentId("agent-1")

    mock_agent1 = Mock(spec=DummyAgent)
    mock_agent1.id = AgentId("agent-1")
    mock_agent1.local_config = AgentUnifiedConfig(
        agent=AgentConfig(backend=AgentBackend.DUMMY, scaling_group="default", id="agent-1"),
        container=ContainerConfig(scratch_type=ScratchType.HOSTDIR),
        resource=ResourceConfig(),
        etcd=EtcdConfig(namespace="test", addr=HostPortPair(host="127.0.0.1", port=2379)),
    )
    # Use the real update_scaling_group method
    mock_agent1.update_scaling_group = lambda scaling_group: AbstractAgent.update_scaling_group(
        mock_agent1, scaling_group
    )

    mock_agent2 = Mock(spec=DummyAgent)
    mock_agent2.id = AgentId("agent-2")
    mock_agent2.local_config = AgentUnifiedConfig(
        agent=AgentConfig(backend=AgentBackend.DUMMY, scaling_group="default", id="agent-2"),
        container=ContainerConfig(scratch_type=ScratchType.HOSTDIR),
        resource=ResourceConfig(),
        etcd=EtcdConfig(namespace="test", addr=HostPortPair(host="127.0.0.1", port=2379)),
    )
    # Use the real update_scaling_group method
    mock_agent2.update_scaling_group = lambda scaling_group: AbstractAgent.update_scaling_group(
        mock_agent2, scaling_group
    )

    server.agents = {
        AgentId("agent-1"): mock_agent1,
        AgentId("agent-2"): mock_agent2,
    }

    with patch("ai.backend.common.config.find_config_file", return_value=config_file):
        await server.update_scaling_group.__wrapped__.__wrapped__(server, "gpu", AgentId("agent-2"))  # type: ignore[attr-defined]

    with open(config_file) as f:
        updated_config = tomlkit.load(f)

    assert updated_config["agents"][1]["agent"]["scaling-group"] == "gpu"  # type: ignore[index]
    assert updated_config["agents"][0]["agent"]["scaling-group"] == "default"  # type: ignore[index]
    assert mock_agent2.local_config.agent.scaling_group == "gpu"
    assert mock_agent1.local_config.agent.scaling_group == "default"
