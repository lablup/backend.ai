from __future__ import annotations

import random
from uuid import uuid4

import pytest

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.types import SessionId


async def test_valkey_live_hset_operations(test_valkey_live: ValkeyLiveClient) -> None:
    """Test hash set operations for scheduler use"""
    test_hash = f"test-hash-{random.randint(1000, 9999)}"

    # Test single field hset
    result = await test_valkey_live.add_scheduler_metadata(
        test_hash,
        {
            "field1": "value1",
        },
    )
    assert result == 1

    # Test multiple field hset with mapping
    result = await test_valkey_live.add_scheduler_metadata(
        test_hash,
        {
            "field2": "value2",
            "field3": "value3",
        },
    )
    assert result == 2


async def test_valkey_live_multiple_data_operations(test_valkey_live: ValkeyLiveClient) -> None:
    """Test multiple live data operations"""
    test_prefix = f"test-multiple-{random.randint(1000, 9999)}"
    keys = [f"{test_prefix}-key-{i}" for i in range(3)]

    # Store some test data first
    for i, key in enumerate(keys):
        await test_valkey_live.store_live_data(key, f"value-{i}")

    # Test getting multiple keys
    results = await test_valkey_live.get_multiple_live_data(keys)
    assert len(results) == 3
    assert all(result is not None for result in results)


class TestCountActiveConnectionsBatch:
    @pytest.fixture()
    async def session_ids_with_active_connections(
        self,
        test_valkey_live: ValkeyLiveClient,
    ) -> list[SessionId]:
        session_ids = [SessionId(uuid4()) for _ in range(3)]
        await test_valkey_live.update_connection_tracker(str(session_ids[0]), "ssh", "stream-1")
        await test_valkey_live.update_connection_tracker(str(session_ids[0]), "ssh", "stream-2")
        await test_valkey_live.update_connection_tracker(str(session_ids[1]), "jupyter", "stream-1")
        return session_ids

    async def test_returns_connection_counts_by_session(
        self,
        test_valkey_live: ValkeyLiveClient,
        session_ids_with_active_connections: list[SessionId],
    ) -> None:
        result = await test_valkey_live.count_active_connections_batch(
            session_ids_with_active_connections
        )

        assert result == {
            session_ids_with_active_connections[0]: 2,
            session_ids_with_active_connections[1]: 1,
            session_ids_with_active_connections[2]: 0,
        }

    async def test_returns_empty_mapping_for_empty_input(
        self,
        test_valkey_live: ValkeyLiveClient,
    ) -> None:
        result = await test_valkey_live.count_active_connections_batch([])

        assert result == {}


async def test_valkey_live_client_lifecycle(test_valkey_live: ValkeyLiveClient) -> None:
    """Test client lifecycle management"""
    # The client should be created and working
    test_key = f"test-lifecycle-{random.randint(1000, 9999)}"
    await test_valkey_live.store_live_data(test_key, "test-value")
    result = await test_valkey_live.get_live_data(test_key)
    assert result is not None

    # Close should work without errors
    await test_valkey_live.close()

    # Second close should not raise an error
    await test_valkey_live.close()
