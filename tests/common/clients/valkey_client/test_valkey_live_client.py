from __future__ import annotations

import random

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient


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
