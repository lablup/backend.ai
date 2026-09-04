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

    state = await test_valkey_rate_limit.consume(user_id, window=60)

    assert state == RateLimitState(count=1, reset=60)


async def test_later_requests_keep_the_window(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    user_id = UserID(uuid.uuid4())
    await test_valkey_rate_limit.consume(user_id, window=60)
    await asyncio.sleep(1.1)

    state = await test_valkey_rate_limit.consume(user_id, window=60)

    assert state == RateLimitState(count=2, reset=59)


async def test_new_window_after_expiry(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    user_id = UserID(uuid.uuid4())
    await test_valkey_rate_limit.consume(user_id, window=1)
    await asyncio.sleep(1.1)

    state = await test_valkey_rate_limit.consume(user_id, window=60)

    assert state == RateLimitState(count=1, reset=60)


async def test_windows_are_keyed_by_user(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    counted_user = UserID(uuid.uuid4())
    other_user = UserID(uuid.uuid4())
    await test_valkey_rate_limit.consume(counted_user, window=60)

    assert await test_valkey_rate_limit.get_state(other_user) is None
