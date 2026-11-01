from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
)
from ai.backend.common.clients.valkey_client.valkey_session.client import (
    LOGIN_FAIL_COUNT_KEY_PREFIX,
    LOGIN_HISTORY_KEY_PREFIX,
    ValkeySessionClient,
)
from ai.backend.common.defs import REDIS_STATISTICS_DB
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import ValkeyTarget

ALLOWED_FAIL_COUNT = 5
BLOCK_SECONDS = 600


@pytest.fixture
def valkey_target(redis_container: tuple[str, HostPortPairModel]) -> ValkeyTarget:
    return ValkeyTarget(addr=redis_container[1].address)


@pytest.fixture
async def session_client(valkey_target: ValkeyTarget) -> AsyncIterator[ValkeySessionClient]:
    client = await ValkeySessionClient.create(
        valkey_target,
        db_id=REDIS_STATISTICS_DB,
        human_readable_name="test.session",
    )
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
async def raw_client(valkey_target: ValkeyTarget) -> AsyncIterator[AbstractValkeyClient]:
    client = create_valkey_client(
        valkey_target=valkey_target,
        db_id=REDIS_STATISTICS_DB,
        human_readable_name="test.session.raw",
    )
    await client.connect()
    try:
        yield client
    finally:
        await client.disconnect()


@pytest.fixture
def username(test_case_ns: str) -> str:
    return f"{test_case_ns}@example.com"


@pytest.fixture
def fail_count_key(username: str) -> str:
    return f"{LOGIN_FAIL_COUNT_KEY_PREFIX}{username}"


async def _get(raw_client: AbstractValkeyClient, key: str) -> bytes | None:
    async with raw_client.client() as conn:
        return await conn.get(key)


async def _ttl(raw_client: AbstractValkeyClient, key: str) -> int:
    async with raw_client.client() as conn:
        return await conn.ttl(key)


class TestReserveLoginAttempt:
    async def test_concurrent_reservations_are_all_counted(
        self,
        session_client: ValkeySessionClient,
        raw_client: AbstractValkeyClient,
        username: str,
        fail_count_key: str,
    ) -> None:
        results = await asyncio.gather(*[
            session_client.reserve_login_attempt(username, 100, BLOCK_SECONDS) for _ in range(20)
        ])

        assert all(results)
        assert await _get(raw_client, fail_count_key) == b"20"

    async def test_concurrent_reservations_stop_at_the_limit(
        self,
        session_client: ValkeySessionClient,
        raw_client: AbstractValkeyClient,
        username: str,
        fail_count_key: str,
    ) -> None:
        results = await asyncio.gather(*[
            session_client.reserve_login_attempt(username, ALLOWED_FAIL_COUNT, BLOCK_SECONDS)
            for _ in range(20)
        ])

        assert results.count(True) == ALLOWED_FAIL_COUNT
        assert await _get(raw_client, fail_count_key) == str(ALLOWED_FAIL_COUNT).encode()

    async def test_reservation_sets_expiration(
        self,
        session_client: ValkeySessionClient,
        raw_client: AbstractValkeyClient,
        username: str,
        fail_count_key: str,
    ) -> None:
        await session_client.reserve_login_attempt(username, ALLOWED_FAIL_COUNT, BLOCK_SECONDS)

        assert 0 < await _ttl(raw_client, fail_count_key) <= BLOCK_SECONDS

    async def test_blocked_attempt_restarts_expiration(
        self,
        session_client: ValkeySessionClient,
        raw_client: AbstractValkeyClient,
        username: str,
        fail_count_key: str,
    ) -> None:
        await session_client.reserve_login_attempt(username, 1, 100)

        assert not await session_client.reserve_login_attempt(username, 1, BLOCK_SECONDS)

        assert await _ttl(raw_client, fail_count_key) > 100


class TestReleaseLoginAttempt:
    async def test_release_takes_back_one_attempt(
        self,
        session_client: ValkeySessionClient,
        raw_client: AbstractValkeyClient,
        username: str,
        fail_count_key: str,
    ) -> None:
        await session_client.reserve_login_attempt(username, ALLOWED_FAIL_COUNT, BLOCK_SECONDS)
        await session_client.reserve_login_attempt(username, ALLOWED_FAIL_COUNT, BLOCK_SECONDS)

        await session_client.release_login_attempt(username)

        assert await _get(raw_client, fail_count_key) == b"1"
        assert await _ttl(raw_client, fail_count_key) > 0

    async def test_releasing_the_last_attempt_removes_the_key(
        self,
        session_client: ValkeySessionClient,
        raw_client: AbstractValkeyClient,
        username: str,
        fail_count_key: str,
    ) -> None:
        await session_client.reserve_login_attempt(username, ALLOWED_FAIL_COUNT, BLOCK_SECONDS)

        await session_client.release_login_attempt(username)

        assert await _get(raw_client, fail_count_key) is None

    async def test_release_without_a_key_does_not_go_negative(
        self,
        session_client: ValkeySessionClient,
        raw_client: AbstractValkeyClient,
        username: str,
        fail_count_key: str,
    ) -> None:
        await session_client.release_login_attempt(username)

        assert await _get(raw_client, fail_count_key) is None


class TestClearLoginBlock:
    async def test_clear_removes_old_and_new_keys(
        self,
        session_client: ValkeySessionClient,
        raw_client: AbstractValkeyClient,
        username: str,
        fail_count_key: str,
    ) -> None:
        history_key = f"{LOGIN_HISTORY_KEY_PREFIX}{username}"
        await session_client.reserve_login_attempt(username, ALLOWED_FAIL_COUNT, BLOCK_SECONDS)
        async with raw_client.client() as conn:
            await conn.set(history_key, '{"last_login_attempt": 1, "login_fail_count": 10}')

        await session_client.clear_login_block(username)

        assert await _get(raw_client, fail_count_key) is None
        assert await _get(raw_client, history_key) is None
