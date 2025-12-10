from collections.abc import AsyncIterator

import pytest

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.typed_validators import HostPortPair
from ai.backend.common.types import ValkeyTarget
from ai.backend.testutils.bootstrap import redis_container  # noqa: F401


@pytest.mark.integration
class TestValkeyStatClient:
    @pytest.fixture
    async def redis_config(self, redis_container) -> RedisConfig:  # noqa: F811
        """Redis config fixture using testcontainer."""
        redis_addr = redis_container[1]
        return RedisConfig(
            addr=HostPortPair(host=redis_addr.host, port=redis_addr.port),
            password=None,
        )

    @pytest.fixture
    async def valkey_stat_client(
        self, redis_config: RedisConfig
    ) -> AsyncIterator[ValkeyStatClient]:
        """Create a ValkeyStatClient instance with real Valkey connection."""
        addr = redis_config.addr
        assert addr is not None
        valkey_target = ValkeyTarget(
            addr=f"{addr.host}:{addr.port}",
            password=redis_config.password,
        )
        client = await ValkeyStatClient.create(
            valkey_target=valkey_target,
            db_id=0,
            human_readable_name="test-valkey-stat-client",
        )
        yield client
        await client.close()

    @pytest.mark.asyncio
    async def test_get_agent_container_counts_as_dict_success(
        self, valkey_stat_client: ValkeyStatClient
    ) -> None:
        """Test successful retrieval of container counts as dictionary."""
        agent_ids = ["agent-1", "agent-2", "agent-3"]
        expected_counts = {
            "agent-1": 5,
            "agent-2": 3,
            "agent-3": 7,
        }

        # Set container counts in Valkey
        for agent_id, count in expected_counts.items():
            await valkey_stat_client.set_agent_container_count(agent_id, count)

        # Retrieve and verify
        result = await valkey_stat_client.get_agent_container_counts_as_dict(agent_ids)

        assert result == expected_counts
        assert len(result) == len(agent_ids)
        for agent_id in agent_ids:
            assert agent_id in result

    @pytest.mark.asyncio
    async def test_get_agent_container_counts_as_dict_with_missing_agents(
        self, valkey_stat_client: ValkeyStatClient
    ) -> None:
        """Test that missing agents return 0 count."""
        agent_ids = ["agent-1", "agent-2", "agent-3"]

        # Only set counts for agent-1 and agent-3
        await valkey_stat_client.set_agent_container_count("agent-1", 5)
        await valkey_stat_client.set_agent_container_count("agent-3", 7)

        result = await valkey_stat_client.get_agent_container_counts_as_dict(agent_ids)

        assert result["agent-1"] == 5
        assert result["agent-2"] == 0  # Missing agent should have count 0
        assert result["agent-3"] == 7

    @pytest.mark.asyncio
    async def test_get_agent_container_counts_as_dict_empty_list(
        self, valkey_stat_client: ValkeyStatClient
    ) -> None:
        """Test that empty agent_ids list returns empty dict."""
        agent_ids: list[str] = []

        result = await valkey_stat_client.get_agent_container_counts_as_dict(agent_ids)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_agent_container_counts_as_dict_all_zeros(
        self, valkey_stat_client: ValkeyStatClient
    ) -> None:
        """Test that agents with 0 containers are correctly handled."""
        agent_ids = ["agent-1", "agent-2"]

        # Set zero counts
        await valkey_stat_client.set_agent_container_count("agent-1", 0)
        await valkey_stat_client.set_agent_container_count("agent-2", 0)

        result = await valkey_stat_client.get_agent_container_counts_as_dict(agent_ids)

        assert result["agent-1"] == 0
        assert result["agent-2"] == 0

    @pytest.mark.asyncio
    async def test_get_agent_container_counts_as_dict_single_agent(
        self, valkey_stat_client: ValkeyStatClient
    ) -> None:
        """Test retrieval for a single agent."""
        agent_ids = ["agent-1"]

        # Set count
        await valkey_stat_client.set_agent_container_count("agent-1", 10)

        result = await valkey_stat_client.get_agent_container_counts_as_dict(agent_ids)

        assert result["agent-1"] == 10
        assert len(result) == 1
