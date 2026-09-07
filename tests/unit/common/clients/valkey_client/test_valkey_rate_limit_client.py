from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from typing import Any

import pytest

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import (
    RateLimitState,
    ValkeyRateLimitClient,
)
from ai.backend.common.data.entity.user import UserID


@dataclass(frozen=True)
class _WindowSubject:
    """A kind of thing a window is keyed by: the call that counts a request for one,
    the subject to count, and another of the same kind whose window must stay its own."""

    description: str
    consumer: str
    counted: Any
    unrelated: Any


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


@pytest.mark.parametrize(
    "subject",
    [
        _WindowSubject(
            description="user",
            consumer="consume_user_rate_limit",
            counted=UserID(uuid.uuid4()),
            unrelated=UserID(uuid.uuid4()),
        ),
        _WindowSubject(
            description="ip",
            consumer="consume_ip_rate_limit",
            counted="10.0.0.1",
            unrelated="10.0.0.2",
        ),
    ],
    ids=lambda subject: subject.description,
)
async def test_the_limit_of_the_open_window_stands(
    test_valkey_rate_limit: ValkeyRateLimitClient,
    subject: _WindowSubject,
) -> None:
    consume = getattr(test_valkey_rate_limit, subject.consumer)
    await consume(subject.counted, window_seconds=60, limit=30000)

    state = await consume(subject.counted, window_seconds=60, limit=10)

    assert state.limit == 30000


@pytest.mark.parametrize(
    "subject",
    [
        _WindowSubject(
            description="user",
            consumer="consume_user_rate_limit",
            counted=UserID(uuid.uuid4()),
            unrelated=UserID(uuid.uuid4()),
        ),
        _WindowSubject(
            description="ip",
            consumer="consume_ip_rate_limit",
            counted="10.0.1.1",
            unrelated="10.0.1.2",
        ),
    ],
    ids=lambda subject: subject.description,
)
async def test_windows_do_not_leak_between_subjects(
    test_valkey_rate_limit: ValkeyRateLimitClient,
    subject: _WindowSubject,
) -> None:
    consume = getattr(test_valkey_rate_limit, subject.consumer)
    await consume(subject.counted, window_seconds=60, limit=30000)

    state = await consume(subject.unrelated, window_seconds=60, limit=30000)

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
