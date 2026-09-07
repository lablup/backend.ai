from __future__ import annotations

import asyncio
import uuid

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import (
    RateLimitState,
    ValkeyRateLimitClient,
)
from ai.backend.common.data.entity.user import UserID


async def test_first_request_opens_the_window(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    key = UserID(uuid.uuid4())

    state = await test_valkey_rate_limit.consume_user_rate_limit(
        key, window_seconds=60, limit=30000
    )

    assert state == RateLimitState(count=1, limit=30000, reset_after_seconds=60)


async def test_later_requests_keep_the_window(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    key = UserID(uuid.uuid4())
    await test_valkey_rate_limit.consume_user_rate_limit(key, window_seconds=60, limit=30000)
    await asyncio.sleep(1.1)

    state = await test_valkey_rate_limit.consume_user_rate_limit(
        key, window_seconds=60, limit=30000
    )

    assert state.count == 2
    assert 0 < state.reset_after_seconds < 60


async def test_count_keeps_growing_past_the_limit(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    key = UserID(uuid.uuid4())
    for _ in range(3):
        await test_valkey_rate_limit.consume_user_rate_limit(key, window_seconds=60, limit=2)

    state = await test_valkey_rate_limit.consume_user_rate_limit(key, window_seconds=60, limit=2)

    assert state.count == 4
    assert state.limit == 2


async def test_a_new_window_takes_the_limit_it_opens_with(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    key = UserID(uuid.uuid4())
    await test_valkey_rate_limit.consume_user_rate_limit(key, window_seconds=1, limit=30000)
    await asyncio.sleep(1.1)

    state = await test_valkey_rate_limit.consume_user_rate_limit(key, window_seconds=60, limit=10)

    assert state == RateLimitState(count=1, limit=10, reset_after_seconds=60)


async def test_the_limit_of_the_open_user_window_stands(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    key = UserID(uuid.uuid4())
    await test_valkey_rate_limit.consume_user_rate_limit(key, window_seconds=60, limit=30000)

    state = await test_valkey_rate_limit.consume_user_rate_limit(key, window_seconds=60, limit=10)

    assert state.limit == 30000


async def test_the_limit_of_the_open_ip_window_stands(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    key = "10.0.0.1"
    await test_valkey_rate_limit.consume_ip_rate_limit(key, window_seconds=60, limit=1000)

    state = await test_valkey_rate_limit.consume_ip_rate_limit(key, window_seconds=60, limit=10)

    assert state.limit == 1000


async def test_user_windows_are_keyed_by_the_user(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    key = UserID(uuid.uuid4())
    other_key = UserID(uuid.uuid4())
    await test_valkey_rate_limit.consume_user_rate_limit(key, window_seconds=60, limit=30000)

    state = await test_valkey_rate_limit.consume_user_rate_limit(
        other_key, window_seconds=60, limit=30000
    )

    assert state.count == 1


async def test_ip_windows_are_keyed_by_the_address(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    key = "10.0.1.1"
    other_key = "10.0.1.2"
    await test_valkey_rate_limit.consume_ip_rate_limit(key, window_seconds=60, limit=1000)

    state = await test_valkey_rate_limit.consume_ip_rate_limit(
        other_key, window_seconds=60, limit=1000
    )

    assert state.count == 1


async def test_a_user_and_an_address_of_the_same_id_hold_separate_windows(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    shared_id = uuid.uuid4()
    await test_valkey_rate_limit.consume_user_rate_limit(
        UserID(shared_id), window_seconds=60, limit=30000
    )

    state = await test_valkey_rate_limit.consume_ip_rate_limit(
        str(shared_id), window_seconds=60, limit=1000
    )

    assert state == RateLimitState(count=1, limit=1000, reset_after_seconds=60)
