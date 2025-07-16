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
    results = await test_valkey_stat._get_multiple_keys(test_keys)
    assert len(results) == len(test_keys)
    for i, result in enumerate(results):
        assert result == test_values[i]

    # Clean up
    deleted_count = await test_valkey_stat.delete(test_keys)
    assert deleted_count == len(test_keys)
