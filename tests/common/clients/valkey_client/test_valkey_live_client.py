from __future__ import annotations

import random

from ai.backend.common.clients.valkey_client import ValkeyLiveClient


async def test_valkey_live_hset_operations(test_valkey_live: ValkeyLiveClient) -> None:
    """Test hash set operations for scheduler use"""
    test_hash = f"test-hash-{random.randint(1000, 9999)}"

    # Test single field hset
    result = await test_valkey_live.hset(test_hash, "field1", "value1")
    assert result == 1

    # Test multiple field hset with mapping
    result = await test_valkey_live.hset(
        test_hash,
        mapping={
            "field2": "value2",
            "field3": "value3",
        },
    )
    assert result == 2


async def test_valkey_live_batch_operations(test_valkey_live: ValkeyLiveClient) -> None:
    """Test batch operations for scheduler use"""
    test_prefix = f"test-batch-{random.randint(1000, 9999)}"
    keys = [f"{test_prefix}-key-{i}" for i in range(3)]

    # Create a batch
    batch = test_valkey_live.create_batch(is_atomic=True)

    # Add delete operations to batch
    batch.delete(keys)

    # Add hash set operations to batch
    for i, key in enumerate(keys):
        batch.hset(f"{key}-hash", {"field": f"hash-value-{i}"})

    # Execute batch
    results = await test_valkey_live.execute_batch(batch)
    assert isinstance(results, list)


async def test_valkey_live_batch_single_delete(test_valkey_live: ValkeyLiveClient) -> None:
    """Test batch operations with single key delete"""
    test_key = f"test-single-{random.randint(1000, 9999)}"

    # Create a batch
    batch = test_valkey_live.create_batch(is_atomic=True)

    # Add single key delete
    batch.delete(test_key)

    # Execute batch
    results = await test_valkey_live.execute_batch(batch)
    assert isinstance(results, list)


async def test_valkey_live_client_lifecycle(test_valkey_live: ValkeyLiveClient) -> None:
    """Test client lifecycle management"""
    # The client should be created and working
    batch = test_valkey_live.create_batch()
    assert batch is not None

    # Close should work without errors
    await test_valkey_live.close()

    # Second close should not raise an error
    await test_valkey_live.close()
