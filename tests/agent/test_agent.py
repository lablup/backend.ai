"""
TODO: rewrite
"""

import os
from unittest.mock import AsyncMock

import pytest

from ai.backend.agent.config.unified import (
    AgentConfig,
    AgentUnifiedConfig,
    ContainerConfig,
    EtcdConfig,
    ResourceConfig,
)
from ai.backend.agent.server import AgentRPCServer
from ai.backend.common.typed_validators import HostPortPair


class Dummy:
    pass


kgid = "kernel-gid"
kuid = "kernel-uid"
ctnr = "container"


@pytest.fixture
async def arpcs_no_ainit(test_id, redis_container):
    etcd = Dummy()
    etcd.get_prefix = None

    # Create a minimal pydantic config for testing
    config = AgentUnifiedConfig(
        agent=AgentConfig(backend="docker"),
        container=ContainerConfig(scratch_type="hostdir"),
        resource=ResourceConfig(),
        etcd=EtcdConfig(namespace="test", addr=HostPortPair(host="127.0.0.1", port=2379)),
    )

    ars = AgentRPCServer(etcd=etcd, local_config=config, skip_detect_manager=True)

    # Mock the runtime object to return the etcd client
    runtime = Dummy()
    runtime.get_etcd = lambda: etcd
    ars.runtime = runtime

    yield ars


@pytest.mark.asyncio
async def test_read_agent_config_container_invalid01(arpcs_no_ainit, mocker):
    inspect_mock = AsyncMock(return_value={"a": 1, "b": 2})
    mocker.patch.object(arpcs_no_ainit.etcd, "get_prefix", new=inspect_mock)
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
    mocker.patch.object(arpcs_no_ainit.etcd, "get_prefix", new=inspect_mock)
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
    mocker.patch.object(arpcs_no_ainit.etcd, "get_prefix", new=inspect_mock)
    await arpcs_no_ainit.read_agent_config_container()

    assert arpcs_no_ainit.local_config.container.kernel_gid.real == 10
    assert (
        arpcs_no_ainit.local_config.container.kernel_uid.real == os.getuid()
    )  # default value (os.getuid())


@pytest.mark.asyncio
async def test_read_agent_config_container_2valid(arpcs_no_ainit, mocker):
    inspect_mock = AsyncMock(return_value={kgid: 10, kuid: 20})
    mocker.patch.object(arpcs_no_ainit.etcd, "get_prefix", new=inspect_mock)
    await arpcs_no_ainit.read_agent_config_container()

    assert arpcs_no_ainit.local_config.container.kernel_gid.real == 10
    assert arpcs_no_ainit.local_config.container.kernel_uid.real == 20
