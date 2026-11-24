from __future__ import annotations

import asyncio
import uuid

import pytest

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import (
    RateLimitState,
    ValkeyRateLimitClient,
)
from ai.backend.common.data.entity.user import UserID


@pytest.fixture
async def user_with_an_open_window(test_valkey_rate_limit: ValkeyRateLimitClient) -> UserID:
    user_id = UserID(uuid.uuid4())
    key = f"user.{user_id}.rate_limit_window"
    async with test_valkey_rate_limit._client.client() as conn:
        await conn.hset(key, {"count": "1", "limit": "30000", "window_seconds": "900"})
        await conn.expire(key, 900)
    return user_id


@pytest.fixture
async def user_with_an_open_window_of_no_stored_length(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> UserID:
    """A window opened by a manager that does not store the window length."""
    user_id = UserID(uuid.uuid4())
    key = f"user.{user_id}.rate_limit_window"
    async with test_valkey_rate_limit._client.client() as conn:
        await conn.hset(key, {"count": "1", "limit": "30000"})
        await conn.expire(key, 900)
    return user_id


async def test_first_request_opens_the_window(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    key = UserID(uuid.uuid4())

    state = await test_valkey_rate_limit.consume_user_rlim_window(
        key, window_seconds=60, limit=30000
    )

    assert state == RateLimitState(count=1, limit=30000, window_seconds=60, reset_after_seconds=60)


async def test_later_requests_keep_the_window(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    key = UserID(uuid.uuid4())
    await test_valkey_rate_limit.consume_user_rlim_window(key, window_seconds=60, limit=30000)
    await asyncio.sleep(1.1)

    state = await test_valkey_rate_limit.consume_user_rlim_window(
        key, window_seconds=60, limit=30000
    )

    assert state.count == 2
    assert 0 < state.reset_after_seconds < 60


async def test_count_keeps_growing_past_the_limit(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    key = UserID(uuid.uuid4())
    for _ in range(3):
        await test_valkey_rate_limit.consume_user_rlim_window(key, window_seconds=60, limit=2)

    state = await test_valkey_rate_limit.consume_user_rlim_window(key, window_seconds=60, limit=2)

    assert state.count == 4
    assert state.limit == 2


async def test_a_new_window_takes_the_limit_it_opens_with(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    key = UserID(uuid.uuid4())
    await test_valkey_rate_limit.consume_user_rlim_window(key, window_seconds=1, limit=30000)
    await asyncio.sleep(1.1)

    state = await test_valkey_rate_limit.consume_user_rlim_window(key, window_seconds=60, limit=10)

    assert state == RateLimitState(count=1, limit=10, window_seconds=60, reset_after_seconds=60)


async def test_the_limit_of_the_open_user_window_stands(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    key = UserID(uuid.uuid4())
    await test_valkey_rate_limit.consume_user_rlim_window(key, window_seconds=60, limit=30000)

    state = await test_valkey_rate_limit.consume_user_rlim_window(key, window_seconds=60, limit=10)

    assert state.limit == 30000


async def test_the_length_of_the_open_window_stands(
    test_valkey_rate_limit: ValkeyRateLimitClient,
    user_with_an_open_window: UserID,
) -> None:
    state = await test_valkey_rate_limit.consume_user_rlim_window(
        user_with_an_open_window, window_seconds=60, limit=30000
    )

    assert state.window_seconds == 900
    assert 60 < state.reset_after_seconds <= 900


async def test_reading_the_window_reports_its_stored_length(
    test_valkey_rate_limit: ValkeyRateLimitClient,
    user_with_an_open_window: UserID,
) -> None:
    state = await test_valkey_rate_limit.get_user_rlim_window(user_with_an_open_window)

    assert state is not None
    assert state.window_seconds == 900


async def test_a_window_without_a_stored_length_reads_as_no_open_window(
    test_valkey_rate_limit: ValkeyRateLimitClient,
    user_with_an_open_window_of_no_stored_length: UserID,
) -> None:
    state = await test_valkey_rate_limit.get_user_rlim_window(
        user_with_an_open_window_of_no_stored_length
    )

    assert state is None


async def test_the_limit_of_the_open_ip_window_stands(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    key = "10.0.0.1"
    await test_valkey_rate_limit.consume_ip_rlim_window(key, window_seconds=60, limit=1000)

    state = await test_valkey_rate_limit.consume_ip_rlim_window(key, window_seconds=60, limit=10)

    assert state.limit == 1000


async def test_user_windows_are_keyed_by_the_user(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    key = UserID(uuid.uuid4())
    other_key = UserID(uuid.uuid4())
    await test_valkey_rate_limit.consume_user_rlim_window(key, window_seconds=60, limit=30000)

    state = await test_valkey_rate_limit.consume_user_rlim_window(
        other_key, window_seconds=60, limit=30000
    )

    assert state.count == 1


async def test_ip_windows_are_keyed_by_the_address(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    key = "10.0.1.1"
    other_key = "10.0.1.2"
    await test_valkey_rate_limit.consume_ip_rlim_window(key, window_seconds=60, limit=1000)

    state = await test_valkey_rate_limit.consume_ip_rlim_window(
        other_key, window_seconds=60, limit=1000
    )

    assert state.count == 1


async def test_a_user_and_an_address_of_the_same_id_hold_separate_windows(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    shared_id = uuid.uuid4()
    await test_valkey_rate_limit.consume_user_rlim_window(
        UserID(shared_id), window_seconds=60, limit=30000
    )

    state = await test_valkey_rate_limit.consume_ip_rlim_window(
        str(shared_id), window_seconds=60, limit=1000
    )

    assert state == RateLimitState(count=1, limit=1000, window_seconds=60, reset_after_seconds=60)
