'''
TODO: rewrite
'''

import pytest

from unittest.mock import AsyncMock

from ai.backend.agent.server import AgentRPCServer


class Dummy:
    pass


kgid = "kernel-gid"
kuid = "kernel-uid"
ctnr = "container"


@pytest.fixture
async def arpcs_no_ainit(test_id, redis_container):
    etcd = Dummy()
    etcd.get_prefix = None
    ars = AgentRPCServer(etcd=etcd, local_config={ctnr: {}}, skip_detect_manager=True)
    yield ars


@pytest.mark.asyncio
async def test_read_agent_config_container_invalid01(arpcs_no_ainit, mocker):
    inspect_mock = AsyncMock(return_value={'a': 1, 'b': 2})
    mocker.patch.object(arpcs_no_ainit.etcd, 'get_prefix', new=inspect_mock)
    await arpcs_no_ainit.read_agent_config_container()
    assert kgid not in arpcs_no_ainit.local_config[ctnr]
    assert kuid not in arpcs_no_ainit.local_config[ctnr]


@pytest.mark.asyncio
async def test_read_agent_config_container_invalid02(arpcs_no_ainit, mocker):
    inspect_mock = AsyncMock(return_value={})
    mocker.patch.object(arpcs_no_ainit.etcd, 'get_prefix', new=inspect_mock)
    await arpcs_no_ainit.read_agent_config_container()
    assert kgid not in arpcs_no_ainit.local_config[ctnr]
    assert kuid not in arpcs_no_ainit.local_config[ctnr]


@pytest.mark.asyncio
async def test_read_agent_config_container_1valid(arpcs_no_ainit, mocker):
    inspect_mock = AsyncMock(return_value={kgid: 10})
    mocker.patch.object(arpcs_no_ainit.etcd, 'get_prefix', new=inspect_mock)
    await arpcs_no_ainit.read_agent_config_container()

    assert arpcs_no_ainit.local_config[ctnr][kgid] == 10
    assert kuid not in arpcs_no_ainit.local_config[ctnr]


@pytest.mark.asyncio
async def test_read_agent_config_container_2valid(arpcs_no_ainit, mocker):
    inspect_mock = AsyncMock(return_value={kgid: 10, kuid: 20})
    mocker.patch.object(arpcs_no_ainit.etcd, 'get_prefix', new=inspect_mock)
    await arpcs_no_ainit.read_agent_config_container()

    assert arpcs_no_ainit.local_config[ctnr][kgid] == 10
    assert arpcs_no_ainit.local_config[ctnr][kuid] == 20
