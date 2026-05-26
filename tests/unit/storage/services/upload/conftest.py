from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from redis.asyncio import Redis

from ai.backend.common import config
from ai.backend.common.clients.valkey_client.valkey_tus import ValkeyTusClient
from ai.backend.common.defs import REDIS_STREAM_LOCK, REDIS_TUS_DB
from ai.backend.common.lock import DistributedLockFactory
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import RedisConnectionInfo, ValkeyTarget
from ai.backend.storage.services.upload.lock import create_tus_lock_factory
from ai.backend.testutils.bootstrap import redis_container  # noqa: F401


@pytest.fixture
async def valkey_tus_client(
    redis_container: tuple[str, HostPortPairModel],  # noqa: F811
) -> AsyncIterator[ValkeyTusClient]:
    hostport_pair = redis_container[1]
    client = await ValkeyTusClient.create(
        ValkeyTarget(addr=hostport_pair.address),
        db_id=REDIS_TUS_DB,
        human_readable_name="test.tus",
    )
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
async def tus_lock_factory(
    redis_container: tuple[str, HostPortPairModel],  # noqa: F811
) -> AsyncIterator[DistributedLockFactory]:
    hostport_pair = redis_container[1]
    lock_redis = RedisConnectionInfo(
        Redis.from_url(f"redis://{hostport_pair.address}/{REDIS_STREAM_LOCK}"),
        sentinel=None,
        name="test.tus.lock",
        service_name=None,
        redis_helper_config=config.redis_helper_default_config,
    )
    try:
        yield create_tus_lock_factory(lock_redis)
    finally:
        await lock_redis.close()
