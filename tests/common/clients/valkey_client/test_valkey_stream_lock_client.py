from __future__ import annotations

import asyncio
import random

from ai.backend.common.clients.valkey_stream.client import ValkeyStreamLockClient


async def test_valkey_stream_lock_ping(test_valkey_stream_lock: ValkeyStreamLockClient) -> None:
    """Test basic ping functionality."""
    result = await test_valkey_stream_lock.ping()
    assert result == "PONG"


async def test_valkey_stream_lock_set_get(test_valkey_stream_lock: ValkeyStreamLockClient) -> None:
    """Test basic set and get operations."""
    test_key = f"test-key-{random.randint(1000, 9999)}"
    test_value = f"test-value-{random.randint(1000, 9999)}"

    # Set value with expiry
    result = await test_valkey_stream_lock.set_with_expiry(test_key, test_value, 60)
    assert result is True

    # Get value
    retrieved_value = await test_valkey_stream_lock.get(test_key)
    assert retrieved_value == test_value

    # Check if key exists
    exists = await test_valkey_stream_lock.exists(test_key)
    assert exists is True


async def test_valkey_stream_lock_expire_operations(
    test_valkey_stream_lock: ValkeyStreamLockClient,
) -> None:
    """Test expire and TTL operations."""
    test_key = f"test-expire-{random.randint(1000, 9999)}"
    test_value = f"test-value-{random.randint(1000, 9999)}"

    # Set value with expiry
    await test_valkey_stream_lock.set_with_expiry(test_key, test_value, 100)

    # Check TTL
    ttl = await test_valkey_stream_lock.ttl(test_key)
    assert ttl > 0
    assert ttl <= 100

    # Update expiry
    result = await test_valkey_stream_lock.expire(test_key, 200)
    assert result is True

    # Check new TTL
    new_ttl = await test_valkey_stream_lock.ttl(test_key)
    assert new_ttl > 100


async def test_valkey_stream_lock_delete(test_valkey_stream_lock: ValkeyStreamLockClient) -> None:
    """Test delete operation."""
    test_key = f"test-delete-{random.randint(1000, 9999)}"
    test_value = f"test-value-{random.randint(1000, 9999)}"

    # Set value
    await test_valkey_stream_lock.set_with_expiry(test_key, test_value, 60)

    # Verify exists
    exists = await test_valkey_stream_lock.exists(test_key)
    assert exists is True

    # Delete
    result = await test_valkey_stream_lock.delete(test_key)
    assert result == 1

    # Verify deleted
    exists = await test_valkey_stream_lock.exists(test_key)
    assert exists is False

    # Delete non-existent key
    result = await test_valkey_stream_lock.delete(f"non-existent-{random.randint(1000, 9999)}")
    assert result == 0


async def test_valkey_stream_lock_default_ttl(
    test_valkey_stream_lock: ValkeyStreamLockClient,
) -> None:
    """Test default TTL behavior."""
    test_key = f"test-default-ttl-{random.randint(1000, 9999)}"
    test_value = f"test-value-{random.randint(1000, 9999)}"

    # Set value without explicit TTL (should use default)
    result = await test_valkey_stream_lock.set_with_expiry(test_key, test_value)
    assert result is True

    # Check TTL is set to default (300 seconds)
    ttl = await test_valkey_stream_lock.ttl(test_key)
    assert ttl > 0
    assert ttl <= 300


async def test_valkey_stream_lock_client_property(
    test_valkey_stream_lock: ValkeyStreamLockClient,
) -> None:
    """Test that client property returns a valid client."""
    client = test_valkey_stream_lock.client
    assert client is not None

    # Test that the client can be used directly
    result = await client.ping()
    assert result == b"PONG"


async def test_valkey_stream_lock_get_nonexistent(
    test_valkey_stream_lock: ValkeyStreamLockClient,
) -> None:
    """Test getting non-existent key."""
    test_key = f"non-existent-{random.randint(1000, 9999)}"

    result = await test_valkey_stream_lock.get(test_key)
    assert result is None

    exists = await test_valkey_stream_lock.exists(test_key)
    assert exists is False


async def test_valkey_stream_lock_concurrent_operations(
    test_valkey_stream_lock: ValkeyStreamLockClient,
) -> None:
    """Test concurrent operations."""
    base_key = f"concurrent-{random.randint(1000, 9999)}"

    async def set_value(index: int) -> None:
        key = f"{base_key}-{index}"
        value = f"value-{index}"
        await test_valkey_stream_lock.set_with_expiry(key, value, 60)

    # Set multiple values concurrently
    tasks = [set_value(i) for i in range(10)]
    await asyncio.gather(*tasks)

    # Verify all values are set
    for i in range(10):
        key = f"{base_key}-{i}"
        value = await test_valkey_stream_lock.get(key)
        assert value == f"value-{i}"

        # Clean up
        await test_valkey_stream_lock.delete(key)
