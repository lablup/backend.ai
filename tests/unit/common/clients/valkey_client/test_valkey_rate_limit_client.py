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

    state = await test_valkey_rate_limit.count_request(user_id, window=60)

    assert state == RateLimitState(count=1, reset=60)


async def test_later_requests_keep_the_window(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    user_id = UserID(uuid.uuid4())
    await test_valkey_rate_limit.count_request(user_id, window=60)
    await asyncio.sleep(1.1)

    state = await test_valkey_rate_limit.count_request(user_id, window=60)

    assert state == RateLimitState(count=2, reset=59)


async def test_new_window_after_expiry(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    user_id = UserID(uuid.uuid4())
    await test_valkey_rate_limit.count_request(user_id, window=1)
    await asyncio.sleep(1.1)

    state = await test_valkey_rate_limit.count_request(user_id, window=60)

    assert state == RateLimitState(count=1, reset=60)


async def test_get_state_reads_the_window_without_counting(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    user_id = UserID(uuid.uuid4())
    await test_valkey_rate_limit.count_request(user_id, window=60)
    await test_valkey_rate_limit.count_request(user_id, window=60)

    state = await test_valkey_rate_limit.get_state(user_id)

    assert state == RateLimitState(count=2, reset=60)
    assert await test_valkey_rate_limit.get_state(user_id) == state


async def test_get_state_without_an_open_window(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    assert await test_valkey_rate_limit.get_state(UserID(uuid.uuid4())) is None


async def test_windows_are_keyed_by_user(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    counted_user = UserID(uuid.uuid4())
    other_user = UserID(uuid.uuid4())
    await test_valkey_rate_limit.count_request(counted_user, window=60)

    assert await test_valkey_rate_limit.get_state(other_user) is None
