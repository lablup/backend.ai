from __future__ import annotations

import asyncio
import re
import uuid
from collections.abc import AsyncIterator

import pytest

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
)
from ai.backend.common.clients.valkey_client.valkey_lock.client import ValkeyLockClient
from ai.backend.common.defs import REDIS_STREAM_LOCK
from ai.backend.common.lock import RedisLock
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import ValkeyTarget


@pytest.fixture
def valkey_target(redis_container: tuple[str, HostPortPairModel]) -> ValkeyTarget:
    return ValkeyTarget(addr=redis_container[1].address)


@pytest.fixture
async def lock_client(valkey_target: ValkeyTarget) -> AsyncIterator[ValkeyLockClient]:
    client = await ValkeyLockClient.create(
        valkey_target,
        db_id=REDIS_STREAM_LOCK,
        human_readable_name="test.lock",
    )
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
async def raw_client(valkey_target: ValkeyTarget) -> AsyncIterator[AbstractValkeyClient]:
    client = create_valkey_client(
        valkey_target=valkey_target,
        db_id=REDIS_STREAM_LOCK,
        human_readable_name="test.lock.raw",
    )
    await client.connect()
    try:
        yield client
    finally:
        await client.disconnect()


@pytest.fixture
def lock_name(test_case_ns: str) -> str:
    return f"{test_case_ns}-lock"


@pytest.fixture
async def held_by_other(raw_client: AbstractValkeyClient, lock_name: str) -> str:
    """The lock key holds another process's token, as redis-py ``Lock`` writes it."""
    token = uuid.uuid1().hex
    async with raw_client.client() as conn:
        await conn.set(lock_name, token)
    return token


async def _get(raw_client: AbstractValkeyClient, key: str) -> bytes | None:
    async with raw_client.client() as conn:
        return await conn.get(key)


async def _pttl(raw_client: AbstractValkeyClient, key: str) -> int:
    async with raw_client.client() as conn:
        return await conn.pttl(key)


class TestRedisLock:
    async def test_acquire_sets_token_under_lock_name(
        self,
        lock_client: ValkeyLockClient,
        raw_client: AbstractValkeyClient,
        lock_name: str,
    ) -> None:
        async with RedisLock(lock_name, lock_client, lifetime=10.0):
            value = await _get(raw_client, lock_name)
            assert value is not None
            assert re.fullmatch(rb"[0-9a-f]{32}", value)
            assert 0 < await _pttl(raw_client, lock_name) <= 10_000
        assert await _get(raw_client, lock_name) is None

    async def test_no_lifetime_sets_no_expiry(
        self,
        lock_client: ValkeyLockClient,
        raw_client: AbstractValkeyClient,
        lock_name: str,
    ) -> None:
        async with RedisLock(lock_name, lock_client, lifetime=None):
            assert await _pttl(raw_client, lock_name) == -1

    async def test_waiter_acquires_after_holder_releases(
        self,
        lock_client: ValkeyLockClient,
        lock_name: str,
    ) -> None:
        holder_released = asyncio.Event()
        order: list[str] = []

        async def waiter() -> None:
            async with RedisLock(lock_name, lock_client, timeout=5.0, lock_retry_interval=0.05):
                assert holder_released.is_set()
                order.append("waiter")

        async with RedisLock(lock_name, lock_client, lifetime=10.0):
            task = asyncio.create_task(waiter())
            await asyncio.sleep(0.2)
            order.append("holder")
            holder_released.set()
        await task
        assert order == ["holder", "waiter"]

    async def test_lock_held_by_other_times_out(
        self,
        lock_client: ValkeyLockClient,
        raw_client: AbstractValkeyClient,
        lock_name: str,
        held_by_other: str,
    ) -> None:
        with pytest.raises(TimeoutError):
            async with RedisLock(lock_name, lock_client, timeout=0.3, lock_retry_interval=0.1):
                pass
        assert await _get(raw_client, lock_name) == held_by_other.encode()

    async def test_zero_timeout_tries_once(
        self,
        lock_client: ValkeyLockClient,
        lock_name: str,
        held_by_other: str,
    ) -> None:
        loop = asyncio.get_running_loop()
        started = loop.time()
        with pytest.raises(TimeoutError):
            async with RedisLock(lock_name, lock_client, timeout=0, lock_retry_interval=1.0):
                pass
        assert loop.time() - started < 0.5

    async def test_release_after_expiry_keeps_other_holder(
        self,
        lock_client: ValkeyLockClient,
        raw_client: AbstractValkeyClient,
        lock_name: str,
    ) -> None:
        other_token = uuid.uuid1().hex
        async with RedisLock(lock_name, lock_client, lifetime=0.2):
            await asyncio.sleep(0.4)
            assert await lock_client.acquire(lock_name, other_token, 10_000)
        assert await _get(raw_client, lock_name) == other_token.encode()
