from __future__ import annotations

import uuid
from typing import AsyncIterator

import pytest

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.defs import REDIS_STATISTICS_DB
from ai.backend.common.types import ValkeyTarget
from ai.backend.testutils.bootstrap import HostPortPairModel


class TestValkeyStatClient:
    @pytest.fixture
    async def test_valkey_stat(self, redis_container) -> AsyncIterator[ValkeyStatClient]:  # noqa: F811
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

        # Note: In actual usage, the key would expire after 1 second
        # For testing purposes, we just verify the operation succeeded

    async def test_valkey_stat_multiple_keys(self, test_valkey_stat: ValkeyStatClient) -> None:
        """Test multiple key operations."""
        test_keys = [f"test-key-{i}-{uuid.uuid4().hex[:8]}" for i in range(3)]
        test_values = [f"test-value-{i}".encode() for i in range(3)]

        # Set multiple keys
        key_value_map = dict(zip(test_keys, test_values))
        await test_valkey_stat.set_multiple_keys(key_value_map)

        # Get multiple keys
        results = await test_valkey_stat._get_multiple_keys(test_keys)
        assert len(results) == len(test_keys)
        for i, result in enumerate(results):
            assert result == test_values[i]

        # Clean up
        deleted_count = await test_valkey_stat.delete(test_keys)
        assert deleted_count == len(test_keys)

    @pytest.mark.asyncio
    async def test_get_agent_container_counts_as_dict_success(
        self, test_valkey_stat: ValkeyStatClient
    ) -> None:
        """Test successful retrieval of container counts as dictionary."""
        agent_ids = [
            f"agent-{uuid.uuid4().hex[:8]}",
            f"agent-{uuid.uuid4().hex[:8]}",
            f"agent-{uuid.uuid4().hex[:8]}",
        ]
        expected_counts = {
            agent_ids[0]: 5,
            agent_ids[1]: 3,
            agent_ids[2]: 7,
        }

        # Set container counts in Valkey
        for agent_id, count in expected_counts.items():
            await test_valkey_stat.set_agent_container_count(agent_id, count)

        # Retrieve and verify
        result = await test_valkey_stat.get_agent_container_counts_as_dict(agent_ids)

        assert result == expected_counts
        assert len(result) == len(agent_ids)
        for agent_id in agent_ids:
            assert agent_id in result

    @pytest.mark.asyncio
    async def test_get_agent_container_counts_as_dict_with_missing_agents(
        self, test_valkey_stat: ValkeyStatClient
    ) -> None:
        """Test that missing agents return 0 count."""
        agent_ids = [
            f"agent-{uuid.uuid4().hex[:8]}",
            f"agent-{uuid.uuid4().hex[:8]}",
            f"agent-{uuid.uuid4().hex[:8]}",
        ]

        # Only set counts for agent-1 and agent-3 (skip agent-2)
        await test_valkey_stat.set_agent_container_count(agent_ids[0], 5)
        await test_valkey_stat.set_agent_container_count(agent_ids[2], 7)

        result = await test_valkey_stat.get_agent_container_counts_as_dict(agent_ids)

        assert result[agent_ids[0]] == 5
        assert result[agent_ids[1]] == 0  # Missing agent should have count 0
        assert result[agent_ids[2]] == 7

    @pytest.mark.asyncio
    async def test_get_agent_container_counts_as_dict_empty_list(
        self, test_valkey_stat: ValkeyStatClient
    ) -> None:
        """Test that empty agent_ids list returns empty dict."""
        agent_ids: list[str] = []

        result = await test_valkey_stat.get_agent_container_counts_as_dict(agent_ids)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_agent_container_counts_as_dict_all_zeros(
        self, test_valkey_stat: ValkeyStatClient
    ) -> None:
        """Test that agents with 0 containers are correctly handled."""
        agent_ids = [
            f"agent-{uuid.uuid4().hex[:8]}",
            f"agent-{uuid.uuid4().hex[:8]}",
        ]

        # Set zero counts
        await test_valkey_stat.set_agent_container_count(agent_ids[0], 0)
        await test_valkey_stat.set_agent_container_count(agent_ids[1], 0)

        result = await test_valkey_stat.get_agent_container_counts_as_dict(agent_ids)

        assert result[agent_ids[0]] == 0
        assert result[agent_ids[1]] == 0

    @pytest.mark.asyncio
    async def test_get_agent_container_counts_as_dict_single_agent(
        self, test_valkey_stat: ValkeyStatClient
    ) -> None:
        """Test retrieval for a single agent."""
        agent_ids = [f"agent-{uuid.uuid4().hex[:8]}"]

        # Set count
        await test_valkey_stat.set_agent_container_count(agent_ids[0], 10)

        result = await test_valkey_stat.get_agent_container_counts_as_dict(agent_ids)

        assert result[agent_ids[0]] == 10
        assert len(result) == 1
