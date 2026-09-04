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
    user_id = UserID(uuid.uuid4())

    state = await test_valkey_rate_limit.consume(user_id, window=60, rate_limit=30000)

    assert state == RateLimitState(count=1, limit=30000, reset=60)


async def test_later_requests_keep_the_limit_of_the_window(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    user_id = UserID(uuid.uuid4())
    await test_valkey_rate_limit.consume(user_id, window=60, rate_limit=30000)
    await asyncio.sleep(1.1)

    state = await test_valkey_rate_limit.consume(user_id, window=60, rate_limit=10)

    assert state.count == 2
    assert state.limit == 30000
    assert 0 < state.reset < 60


async def test_count_keeps_growing_past_the_limit(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    user_id = UserID(uuid.uuid4())
    for _ in range(3):
        await test_valkey_rate_limit.consume(user_id, window=60, rate_limit=2)

    state = await test_valkey_rate_limit.consume(user_id, window=60, rate_limit=2)

    assert state.count == 4
    assert state.limit == 2


async def test_window_without_a_limit(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    user_id = UserID(uuid.uuid4())

    state = await test_valkey_rate_limit.consume(user_id, window=60)

    assert state == RateLimitState(count=1, limit=None, reset=60)


async def test_new_window_takes_the_current_limit(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    user_id = UserID(uuid.uuid4())
    await test_valkey_rate_limit.consume(user_id, window=1, rate_limit=30000)
    await asyncio.sleep(1.1)

    state = await test_valkey_rate_limit.consume(user_id, window=60, rate_limit=10)

    assert state == RateLimitState(count=1, limit=10, reset=60)


async def test_windows_are_keyed_by_user(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    counted_user = UserID(uuid.uuid4())
    other_user = UserID(uuid.uuid4())
    await test_valkey_rate_limit.consume(counted_user, window=60, rate_limit=30000)

    assert await test_valkey_rate_limit.get_state(other_user) is None
