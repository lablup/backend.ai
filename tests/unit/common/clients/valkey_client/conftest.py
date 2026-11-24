from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

import pytest

from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    ValkeyArtifactDownloadTrackingClient,
)
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import ValkeyRateLimitClient
from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.defs import (
    REDIS_LIVE_DB,
    REDIS_RATE_LIMIT_DB,
    REDIS_STATISTICS_DB,
    REDIS_STREAM_DB,
)
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import ValkeyTarget

if TYPE_CHECKING:
    from ai.backend.testutils.bootstrap import RedisContainerFixture


@pytest.fixture
async def test_valkey_live(
    redis_container: RedisContainerFixture,
) -> AsyncIterator[ValkeyLiveClient]:
    hostport_pair: HostPortPairModel = redis_container[1]
    valkey_target = ValkeyTarget(
        addr=hostport_pair.address,
    )
    client = await ValkeyLiveClient.create(
        valkey_target,
        human_readable_name="test.live",
        db_id=REDIS_LIVE_DB,
    )
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
async def test_valkey_stream(
    redis_container: RedisContainerFixture,
) -> AsyncIterator[ValkeyStreamClient]:
    hostport_pair: HostPortPairModel = redis_container[1]
    valkey_target = ValkeyTarget(
        addr=hostport_pair.address,
    )
    client = await ValkeyStreamClient.create(
        valkey_target,
        human_readable_name="event_producer.stream",
        db_id=REDIS_STREAM_DB,
        pubsub_channels={"test-broadcast"},
    )
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
async def test_valkey_rate_limit(
    redis_container: RedisContainerFixture,
) -> AsyncIterator[ValkeyRateLimitClient]:
    hostport_pair: HostPortPairModel = redis_container[1]
    valkey_target = ValkeyTarget(
        addr=hostport_pair.address,
    )
    client = await ValkeyRateLimitClient.create(
        valkey_target,
        human_readable_name="test.rate_limit",
        db_id=REDIS_RATE_LIMIT_DB,
    )
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
async def test_valkey_artifact(
    redis_container: RedisContainerFixture,
) -> AsyncIterator[ValkeyArtifactDownloadTrackingClient]:
    hostport_pair: HostPortPairModel = redis_container[1]
    valkey_target = ValkeyTarget(
        addr=hostport_pair.address,
    )
    client = await ValkeyArtifactDownloadTrackingClient.create(
        valkey_target,
        human_readable_name="test.artifact",
        db_id=REDIS_STATISTICS_DB,
    )
    try:
        yield client
    finally:
        await client.close()
