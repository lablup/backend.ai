from __future__ import annotations

import asyncio
import functools
import uuid
from collections.abc import Awaitable, Callable

import pytest

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import (
    RateLimitState,
    ValkeyRateLimitClient,
)
from ai.backend.common.data.entity.user import UserID


@pytest.fixture
def consume_for_user(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> Callable[..., Awaitable[RateLimitState]]:
    """Counts a request against one user's window."""
    return functools.partial(test_valkey_rate_limit.consume_user_rate_limit, UserID(uuid.uuid4()))


@pytest.fixture
def consume_for_other_user(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> Callable[..., Awaitable[RateLimitState]]:
    """Counts a request against a different user's window."""
    return functools.partial(test_valkey_rate_limit.consume_user_rate_limit, UserID(uuid.uuid4()))


@pytest.fixture
def consume_for_ip(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> Callable[..., Awaitable[RateLimitState]]:
    """Counts a request against one address's window."""
    return functools.partial(test_valkey_rate_limit.consume_ip_rate_limit, "10.0.0.1")


@pytest.fixture
def consume_for_other_ip(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> Callable[..., Awaitable[RateLimitState]]:
    """Counts a request against a different address's window."""
    return functools.partial(test_valkey_rate_limit.consume_ip_rate_limit, "10.0.0.2")


@pytest.fixture
def consume(request: pytest.FixtureRequest) -> Callable[..., Awaitable[RateLimitState]]:
    """The call named by the parametrized fixture."""
    consume: Callable[..., Awaitable[RateLimitState]] = request.getfixturevalue(request.param)
    return consume


@pytest.fixture
def consume_for_other_subject(
    request: pytest.FixtureRequest,
) -> Callable[..., Awaitable[RateLimitState]]:
    """The same call for a different subject of the same kind."""
    consume: Callable[..., Awaitable[RateLimitState]] = request.getfixturevalue(request.param)
    return consume


async def test_first_request_opens_the_window(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    user_id = UserID(uuid.uuid4())

    state = await test_valkey_rate_limit.consume_user_rate_limit(
        user_id, window_seconds=60, limit=30000
    )

    assert state == RateLimitState(count=1, limit=30000, reset_after_seconds=60)


async def test_later_requests_keep_the_window(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    user_id = UserID(uuid.uuid4())
    await test_valkey_rate_limit.consume_user_rate_limit(user_id, window_seconds=60, limit=30000)
    await asyncio.sleep(1.1)

    state = await test_valkey_rate_limit.consume_user_rate_limit(
        user_id, window_seconds=60, limit=30000
    )

    assert state.count == 2
    assert 0 < state.reset_after_seconds < 60


async def test_count_keeps_growing_past_the_limit(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    user_id = UserID(uuid.uuid4())
    for _ in range(3):
        await test_valkey_rate_limit.consume_user_rate_limit(user_id, window_seconds=60, limit=2)

    state = await test_valkey_rate_limit.consume_user_rate_limit(
        user_id, window_seconds=60, limit=2
    )

    assert state.count == 4
    assert state.limit == 2


async def test_a_new_window_takes_the_limit_it_opens_with(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    user_id = UserID(uuid.uuid4())
    await test_valkey_rate_limit.consume_user_rate_limit(user_id, window_seconds=1, limit=30000)
    await asyncio.sleep(1.1)

    state = await test_valkey_rate_limit.consume_user_rate_limit(
        user_id, window_seconds=60, limit=10
    )

    assert state == RateLimitState(count=1, limit=10, reset_after_seconds=60)


@pytest.mark.parametrize("consume", ["consume_for_user", "consume_for_ip"], indirect=True)
async def test_the_limit_of_the_open_window_stands(
    consume: Callable[..., Awaitable[RateLimitState]],
) -> None:
    await consume(window_seconds=60, limit=30000)

    state = await consume(window_seconds=60, limit=10)

    assert state.limit == 30000


@pytest.mark.parametrize(
    ("consume", "consume_for_other_subject"),
    [
        ("consume_for_user", "consume_for_other_user"),
        ("consume_for_ip", "consume_for_other_ip"),
    ],
    indirect=True,
)
async def test_windows_are_keyed_by_their_subject(
    consume: Callable[..., Awaitable[RateLimitState]],
    consume_for_other_subject: Callable[..., Awaitable[RateLimitState]],
) -> None:
    await consume(window_seconds=60, limit=30000)

    state = await consume_for_other_subject(window_seconds=60, limit=30000)

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
