import json
from unittest import mock

import pytest

from aioresponses import aioresponses
from ai.backend.agent.vendor import linux

# TODO: write tests for KernelResourceSpec (read/write consistency)
# from ai.backend.agent.resources import (
#     KernelResourceSpec,
# )

# TODO: write tests for DiscretePropertyAllocMap, FractionAllocMap


def test_node_of_cpu():
    numa = linux.libnuma()

    # When NUMA is not supported.
    linux._numa_supported = False
    assert numa.node_of_cpu(5) == 0

    # When NUMA is supported.
    original_numa_supported = linux._numa_supported
    linux._numa_supported = True
    with mock.patch.object(linux, '_libnuma', create=True) \
            as mock_libnuma:
        numa.node_of_cpu(5)
        mock_libnuma.numa_node_of_cpu.assert_called_once_with(5)

    linux._numa_supported = original_numa_supported


def test_num_nodes():
    numa = linux.libnuma()

    # When NUMA is not supported.
    linux._numa_supported = False
    assert numa.num_nodes() == 1

    # When NUMA is supported.
    original_numa_supported = linux._numa_supported
    linux._numa_supported = True
    with mock.patch.object(linux, '_libnuma', create=True) \
            as mock_libnuma:
        numa.num_nodes()
        mock_libnuma.numa_num_configured_nodes.assert_called_once_with()

    linux._numa_supported = original_numa_supported


@pytest.mark.skip(reason='aioresponses 0.7 is incompatible with aiohttp 3.7+')
@pytest.mark.asyncio
async def test_get_available_cores_without_docker(monkeypatch):

    def mock_sched_getaffinity(pid):
        raise AttributeError

    def mock_sched_getaffinity2(pid):
        return {0, 1}

    numa = linux.libnuma()
    with aioresponses() as m:
        m.get('http://docker/info', body=json.dumps({
            'NCPU': 4,
        }))

        monkeypatch.setattr(linux.os, 'sched_getaffinity',
                            mock_sched_getaffinity,
                            raising=False)
        monkeypatch.setattr(linux.os, 'cpu_count', lambda: 4)
        numa.get_available_cores.cache_clear()
        assert (await numa.get_available_cores()) == {0, 1, 2, 3}

        monkeypatch.setattr(linux.os, 'sched_getaffinity',
                            mock_sched_getaffinity2,
                            raising=False)
        numa.get_available_cores.cache_clear()
        assert (await numa.get_available_cores()) == {0, 1}


@pytest.mark.asyncio
async def test_get_core_topology(mocker):
    mocker.patch.object(linux.libnuma, 'num_nodes', return_value=2)
    mocker.patch.object(linux.libnuma, 'get_available_cores',
                        new=mock.AsyncMock(return_value={0, 1, 2, 3}))
    mocker.patch.object(linux.libnuma, 'node_of_cpu', new=lambda n: n % 2 == 1)

    numa = linux.libnuma()
    assert (await numa.get_core_topology()) == ([0, 2], [1, 3])
