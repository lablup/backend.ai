from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.defs import REDIS_STATISTICS_DB
from ai.backend.common.types import AgentId, ValkeyTarget
from ai.backend.testutils.bootstrap import HostPortPairModel


class TestValkeyStatClient:
    @pytest.fixture
    async def test_valkey_stat(self, redis_container) -> AsyncIterator[ValkeyStatClient]:
        hostport_pair: HostPortPairModel = redis_container[1]
        valkey_target = ValkeyTarget(
            addr=hostport_pair.address,
        )
        client = await ValkeyStatClient.create(
            valkey_target,
            human_readable_name="test.stat",
            db_id=REDIS_STATISTICS_DB,
        )
        try:
            yield client
        finally:
            await client.close()

    async def test_valkey_stat_expiration(self, test_valkey_stat: ValkeyStatClient) -> None:
        """Test key expiration functionality."""
        test_key = f"test-key-exp-{uuid.uuid4().hex[:8]}"
        test_value = b"test-value-exp"

        # Set with custom expiration
        await test_valkey_stat.set(test_key, test_value, expire_sec=1)

        # Verify key exists immediately
        result = await test_valkey_stat._get_raw(test_key)
        assert result == test_value

    async def test_valkey_stat_multiple_keys(self, test_valkey_stat: ValkeyStatClient) -> None:
        """Test multiple key operations."""
        test_keys = [f"test-key-{i}-{uuid.uuid4().hex[:8]}" for i in range(3)]
        test_values = [f"test-value-{i}".encode() for i in range(3)]

        # Set multiple keys
        key_value_map = dict(zip(test_keys, test_values, strict=True))
        await test_valkey_stat.set_multiple_keys(key_value_map)

        # Get multiple keys
        results = await test_valkey_stat._get_multiple_keys(test_keys)
        assert len(results) == len(test_keys)
        for i, result in enumerate(results):
            assert result == test_values[i]

        # Clean up
        deleted_count = await test_valkey_stat.delete(test_keys)
        assert deleted_count == len(test_keys)

    @dataclass
    class _ContainerCountTestCase:
        """Test case for get_agent_container_counts_as_dict."""

        id: str
        agent_count: int
        counts_to_set: dict[int, int]  # {agent_index: count_value}
        expected_counts: dict[int, int]  # {agent_index: expected_count}

    @pytest.mark.parametrize(
        "test_case",
        [
            _ContainerCountTestCase(
                id="success",
                agent_count=3,
                counts_to_set={0: 5, 1: 3, 2: 7},
                expected_counts={0: 5, 1: 3, 2: 7},
            ),
            _ContainerCountTestCase(
                id="missing_agents",
                agent_count=3,
                counts_to_set={0: 5, 2: 7},  # agent[1] missing
                expected_counts={0: 5, 1: 0, 2: 7},  # missing returns 0
            ),
            _ContainerCountTestCase(
                id="all_zeros",
                agent_count=2,
                counts_to_set={0: 0, 1: 0},
                expected_counts={0: 0, 1: 0},
            ),
            _ContainerCountTestCase(
                id="single_agent",
                agent_count=1,
                counts_to_set={0: 10},
                expected_counts={0: 10},
            ),
        ],
        ids=lambda tc: tc.id,
    )
    async def test_get_agent_container_counts_as_dict(
        self, test_valkey_stat: ValkeyStatClient, test_case: _ContainerCountTestCase
    ) -> None:
        """Test retrieval of container counts as dictionary."""
        agent_ids = [AgentId(f"agent-{uuid.uuid4().hex[:8]}") for _ in range(test_case.agent_count)]

        for idx, count in test_case.counts_to_set.items():
            await test_valkey_stat.set_agent_container_count(agent_ids[idx], count)

        result = await test_valkey_stat.get_agent_container_counts_as_dict(agent_ids)

        assert len(result) == test_case.agent_count
        for idx, expected in test_case.expected_counts.items():
            assert result[agent_ids[idx]] == expected

    async def test_get_agent_container_counts_as_dict_empty_list(
        self, test_valkey_stat: ValkeyStatClient
    ) -> None:
        """Test that empty agent_ids list returns empty dict."""
        result = await test_valkey_stat.get_agent_container_counts_as_dict([])
        assert result == {}
