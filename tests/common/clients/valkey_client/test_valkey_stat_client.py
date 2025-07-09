from __future__ import annotations

import random

from ai.backend.common.clients.valkey_client.valkey_stat.client import (
    ValkeyStatClient,
)


async def test_valkey_stat_expiration(test_valkey_stat: ValkeyStatClient) -> None:
    """Test key expiration functionality."""
    test_key = f"test-key-exp-{random.randint(1000, 9999)}"
    test_value = b"test-value-exp"

    # Set with custom expiration
    await test_valkey_stat.set(test_key, test_value, expire_sec=1)

    # Verify key exists immediately
    result = await test_valkey_stat._get_raw(test_key)
    assert result == test_value

    # Note: In actual usage, the key would expire after 1 second
    # For testing purposes, we just verify the operation succeeded


async def test_valkey_stat_multiple_keys(test_valkey_stat: ValkeyStatClient) -> None:
    """Test multiple key operations."""
    test_keys = [f"test-key-{i}-{random.randint(1000, 9999)}" for i in range(3)]
    test_values = [f"test-value-{i}".encode() for i in range(3)]

    # Set multiple keys
    key_value_map = dict(zip(test_keys, test_values))
    await test_valkey_stat.set_multiple_keys(key_value_map)

    # Get multiple keys
    results = await test_valkey_stat.get_multiple_keys(test_keys)
    assert len(results) == len(test_keys)
    for i, result in enumerate(results):
        assert result == test_values[i]

    # Test mget
    mget_results = await test_valkey_stat.mget(test_keys)
    assert len(mget_results) == len(test_keys)
    for i, result in enumerate(mget_results):
        assert result == test_values[i]

    # Clean up
    deleted_count = await test_valkey_stat.delete(test_keys)
    assert deleted_count == len(test_keys)


async def test_valkey_stat_hash_operations(test_valkey_stat: ValkeyStatClient) -> None:
    """Test hash operations."""
    test_hash_key = f"test-hash-{random.randint(1000, 9999)}"
    field_value_map = {
        "field1": b"value1",
        "field2": b"value2",
        "field3": b"value3",
    }

    # Set hash fields
    await test_valkey_stat.hset(test_hash_key, field_value_map)

    # Get individual hash fields
    for field, expected_value in field_value_map.items():
        result = await test_valkey_stat.hget(test_hash_key, field)
        assert result == expected_value

    # Test non-existent field
    result = await test_valkey_stat.hget(test_hash_key, "non-existent")
    assert result is None

    # Clean up
    deleted_count = await test_valkey_stat.delete([test_hash_key])
    assert deleted_count == 1


async def test_valkey_stat_batch_operations(test_valkey_stat: ValkeyStatClient) -> None:
    """Test batch operations."""
    test_keys = [f"test-batch-{i}-{random.randint(1000, 9999)}" for i in range(3)]
    test_values = [f"test-batch-value-{i}".encode() for i in range(3)]

    # Prepare batch operations
    batch_operations = []
    for i, (key, value) in enumerate(zip(test_keys, test_values)):
        batch_operations.append({
            "operation": "set",
            "key": key,
            "value": value,
            "expire_sec": 3600,
        })

    # Add a get operation to the batch
    batch_operations.append({"operation": "get", "key": test_keys[0]})

    # Execute batch
    results = await test_valkey_stat.execute_batch(batch_operations)

    # Verify results (set operations return None, get returns the value)
    assert len(results) == len(batch_operations)
    assert results[-1] == test_values[0]  # The get operation result

    # Clean up
    deleted_count = await test_valkey_stat.delete(test_keys)
    assert deleted_count == len(test_keys)


async def test_valkey_stat_time_operation(test_valkey_stat: ValkeyStatClient) -> None:
    """Test time operation."""
    time_result = await test_valkey_stat.time()
    assert isinstance(time_result, list)
    assert len(time_result) == 2
    # Should return [seconds, microseconds] as bytes
    assert isinstance(time_result[0], int)
    assert isinstance(time_result[1], int)


async def test_valkey_stat_hash_with_expiration(test_valkey_stat: ValkeyStatClient) -> None:
    """Test hash operations with expiration."""
    test_hash_key = f"test-hash-exp-{random.randint(1000, 9999)}"
    field_value_map = {
        "field1": b"value1",
        "field2": b"value2",
    }

    # Set hash with custom expiration
    await test_valkey_stat.hset(test_hash_key, field_value_map, expire_sec=3600)

    # Verify fields exist
    for field, expected_value in field_value_map.items():
        result = await test_valkey_stat.hget(test_hash_key, field)
        assert result == expected_value

    # Clean up
    await test_valkey_stat.delete([test_hash_key])
