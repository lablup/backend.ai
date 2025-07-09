from __future__ import annotations

import random
import time

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import (
    ValkeyRateLimitClient,
)


async def test_valkey_rate_limit_set_and_get(test_valkey_rate_limit: ValkeyRateLimitClient) -> None:
    """Test basic set and get operations with expiration."""
    key = f"test-key-{random.randint(1000, 9999)}"
    value = f"test-value-{random.randint(1000, 9999)}"

    # Set a key with custom expiration
    await test_valkey_rate_limit.set_with_expiration(key, value, 60)

    # Get the key and verify
    result = await test_valkey_rate_limit.get_key(key)
    assert result == value

    # Clean up
    await test_valkey_rate_limit.delete_key(key)


async def test_valkey_rate_limit_increment(test_valkey_rate_limit: ValkeyRateLimitClient) -> None:
    """Test increment operation with expiration."""
    key = f"test-counter-{random.randint(1000, 9999)}"

    # Increment the counter
    result1 = await test_valkey_rate_limit.increment_with_expiration(key, 60)
    assert result1 == 1

    # Increment again
    result2 = await test_valkey_rate_limit.increment_with_expiration(key, 60)
    assert result2 == 2

    # Clean up
    await test_valkey_rate_limit.delete_key(key)


async def test_valkey_rate_limit_rolling_count(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    """Test rolling count operations using sorted sets."""
    access_key = f"test-access-{random.randint(1000, 9999)}"
    now = time.time()

    # Add some entries to the sorted set
    await test_valkey_rate_limit.add_to_sorted_set_with_expiration(
        access_key, now, f"req-{random.randint(1000, 9999)}", 60
    )
    await test_valkey_rate_limit.add_to_sorted_set_with_expiration(
        access_key, now + 1, f"req-{random.randint(1000, 9999)}", 60
    )
    await test_valkey_rate_limit.add_to_sorted_set_with_expiration(
        access_key, now + 2, f"req-{random.randint(1000, 9999)}", 60
    )

    # Get rolling count
    count = await test_valkey_rate_limit.get_rolling_count(access_key)
    assert count == 3

    # Remove expired entries (older than 1 second ago)
    await test_valkey_rate_limit.remove_expired_entries(access_key, now + 1.5, 1)

    # Check count after removal
    count_after_removal = await test_valkey_rate_limit.get_rolling_count(access_key)
    assert count_after_removal == 2  # Should have 2 entries left

    # Clean up
    await test_valkey_rate_limit.delete_key(access_key)


async def test_valkey_rate_limit_logic_execution(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    """Test rate limiting logic execution."""
    access_key = f"test-logic-{random.randint(1000, 9999)}"

    # Execute the rate limiting logic
    result = await test_valkey_rate_limit.execute_rate_limit_logic(
        access_key=access_key,
        window=60,
    )

    assert result == 1  # First request should return 1

    # Execute again
    result2 = await test_valkey_rate_limit.execute_rate_limit_logic(
        access_key=access_key,
        window=60,
    )

    assert result2 == 2  # Second request should return 2

    # Clean up
    await test_valkey_rate_limit.delete_key(access_key)
    await test_valkey_rate_limit.delete_key("__request_id")


async def test_valkey_rate_limit_delete_key(test_valkey_rate_limit: ValkeyRateLimitClient) -> None:
    """Test key deletion."""
    key = f"test-delete-{random.randint(1000, 9999)}"
    value = f"test-value-{random.randint(1000, 9999)}"

    # Set a key
    await test_valkey_rate_limit.set_with_expiration(key, value, 60)

    # Verify it exists
    result = await test_valkey_rate_limit.get_key(key)
    assert result == value

    # Delete the key
    deleted = await test_valkey_rate_limit.delete_key(key)
    assert deleted is True

    # Verify it's gone
    result = await test_valkey_rate_limit.get_key(key)
    assert result is None

    # Try to delete non-existent key
    deleted = await test_valkey_rate_limit.delete_key(key)
    assert deleted is False


async def test_valkey_rate_limit_nonexistent_key(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    """Test operations on non-existent keys."""
    nonexistent_key = f"nonexistent-{random.randint(1000, 9999)}"

    # Get non-existent key
    result = await test_valkey_rate_limit.get_key(nonexistent_key)
    assert result is None

    # Get rolling count for non-existent key
    count = await test_valkey_rate_limit.get_rolling_count(nonexistent_key)
    assert count == 0
