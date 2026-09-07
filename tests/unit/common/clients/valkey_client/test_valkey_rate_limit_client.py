from __future__ import annotations

import asyncio
import functools
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import pytest

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import (
    RateLimitState,
    ValkeyRateLimitClient,
)
from ai.backend.common.data.entity.user import UserID

type ConsumeWindow = Callable[..., Awaitable[RateLimitState]]


@dataclass(frozen=True)
class Window:
    """The calls that count a request for two subjects of one kind: the one a test
    counts against, and another whose window must stay its own."""

    counted: ConsumeWindow
    unrelated: ConsumeWindow


@pytest.fixture
def user_window(test_valkey_rate_limit: ValkeyRateLimitClient) -> Window:
    """Windows keyed by user."""
    return Window(
        counted=functools.partial(
            test_valkey_rate_limit.consume_user_rate_limit, UserID(uuid.uuid4())
        ),
        unrelated=functools.partial(
            test_valkey_rate_limit.consume_user_rate_limit, UserID(uuid.uuid4())
        ),
    )


@pytest.fixture
def ip_window(test_valkey_rate_limit: ValkeyRateLimitClient) -> Window:
    """Windows keyed by client address."""
    return Window(
        counted=functools.partial(test_valkey_rate_limit.consume_ip_rate_limit, "10.0.0.1"),
        unrelated=functools.partial(test_valkey_rate_limit.consume_ip_rate_limit, "10.0.0.2"),
    )


@pytest.fixture
def window(request: pytest.FixtureRequest) -> Window:
    """The window kind named by the parametrized fixture."""
    window: Window = request.getfixturevalue(request.param)
    return window


async def test_first_request_opens_the_window(user_window: Window) -> None:
    state = await user_window.counted(window_seconds=60, limit=30000)

    assert state == RateLimitState(count=1, limit=30000, reset_after_seconds=60)


async def test_later_requests_keep_the_window(user_window: Window) -> None:
    await user_window.counted(window_seconds=60, limit=30000)
    await asyncio.sleep(1.1)

    state = await user_window.counted(window_seconds=60, limit=30000)

    assert state.count == 2
    assert 0 < state.reset_after_seconds < 60


async def test_count_keeps_growing_past_the_limit(user_window: Window) -> None:
    for _ in range(3):
        await user_window.counted(window_seconds=60, limit=2)

    state = await user_window.counted(window_seconds=60, limit=2)

    assert state.count == 4
    assert state.limit == 2


async def test_a_new_window_takes_the_limit_it_opens_with(user_window: Window) -> None:
    await user_window.counted(window_seconds=1, limit=30000)
    await asyncio.sleep(1.1)

    state = await user_window.counted(window_seconds=60, limit=10)

    assert state == RateLimitState(count=1, limit=10, reset_after_seconds=60)


@pytest.mark.parametrize("window", ["user_window", "ip_window"], indirect=True)
async def test_the_limit_of_the_open_window_stands(window: Window) -> None:
    await window.counted(window_seconds=60, limit=30000)

    state = await window.counted(window_seconds=60, limit=10)

    assert state.limit == 30000


@pytest.mark.parametrize("window", ["user_window", "ip_window"], indirect=True)
async def test_windows_are_keyed_by_their_subject(window: Window) -> None:
    await window.counted(window_seconds=60, limit=30000)

    state = await window.unrelated(window_seconds=60, limit=30000)

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
