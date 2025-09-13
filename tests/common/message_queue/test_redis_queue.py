import asyncio
import random

import pytest

from ai.backend.common import redis_helper
from ai.backend.common.defs import REDIS_STREAM_DB
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.message_queue.types import MQMessage
from ai.backend.common.types import (
    RedisHelperConfig,
    RedisTarget,
)


@pytest.fixture
async def redis_conn(redis_container):
    # Configure test Redis connection
    conn = redis_helper.get_redis_object(
        RedisTarget(
            addr=redis_container[1],
            redis_helper_config=RedisHelperConfig(
                socket_timeout=1.0,
                socket_connect_timeout=1.0,
                reconnect_poll_timeout=1.0,
                max_connections=10,
                connection_ready_timeout=1.0,
            ),
        ),
        name="test-redis",
    )
    yield conn
    # Cleanup after tests
    await conn.client.flushdb()
    await conn.close()


@pytest.fixture
def queue_args() -> RedisMQArgs:
    return RedisMQArgs(
        anycast_stream_key="test-stream",
        broadcast_channel="test-broadcast",
        consume_stream_keys={
            "test-stream",
        },
        subscribe_channels={
            "test-broadcast",
        },
        group_name="test-group",
        node_id="test-node",
        db=REDIS_STREAM_DB,
    )


@pytest.fixture(scope="function")
async def redis_queue(redis_container, queue_args: RedisMQArgs):
    # Create consumer group if not exists
    redis_target = RedisTarget(
        addr=redis_container[1],
        redis_helper_config={
            "socket_timeout": 5.0,
            "socket_connect_timeout": 2.0,
            "reconnect_poll_timeout": 0.3,
        },
    )
    queue = await RedisQueue.create(redis_target, queue_args)
    yield queue
    await queue._anycaster._client._client.client.flushdb()  # type: ignore[attr-defined]
    await queue._broadcaster._client._client.client.flushdb()  # type: ignore[attr-defined]
    await queue._consumer._client._client.client.flushdb()  # type: ignore[attr-defined]
    await queue._subscriber._client._client.client.flushdb()  # type: ignore[attr-defined]
    await queue.close()


async def test_send_and_consume(redis_queue: RedisQueue):
    # Test message sending and consuming
    test_payload = {b"key": b"value", b"key2": b"value2"}

    # Send message
    await redis_queue.send(test_payload)

    # Consume message
    async for message in redis_queue.consume_queue():
        assert isinstance(message, MQMessage)
        assert message.payload == test_payload
        await redis_queue.done(message.msg_id)
        break


async def test_subscribe(redis_queue: RedisQueue):
    # Test message subscription
    test_payload = {"key": "value", "key2": "value2"}

    # Create task to subscribe
    received_messages: list[MQMessage] = []

    async def subscriber():
        async for message in redis_queue.subscribe_queue():
            received_messages.append(message)
            if len(received_messages) >= 1:
                break

    subscriber_task = asyncio.create_task(subscriber())
    await asyncio.sleep(0.1)  # Allow subscriber to start

    # Send message
    await redis_queue.broadcast(test_payload)

    # Wait for message to be received
    await asyncio.wait_for(subscriber_task, timeout=5)

    assert len(received_messages) == 1
    assert received_messages[0].payload == test_payload


async def test_broadcast_with_cache(redis_queue: RedisQueue):
    # Test broadcasting with cache
    test_payload = {"key": "value", "key2": "value2"}
    cache_id = f"test-cache-id-{random.randint(1000, 9999)}"

    received_messages: list[MQMessage] = []

    async def subscriber():
        async for message in redis_queue.subscribe_queue():
            received_messages.append(message)
            if len(received_messages) >= 1:
                break

    subscriber_task = asyncio.create_task(subscriber())
    await asyncio.sleep(0.1)  # Allow subscriber to start

    # Broadcast message with cache
    await redis_queue.broadcast_with_cache(cache_id, test_payload)

    # Wait for message to be received
    await asyncio.wait_for(subscriber_task, timeout=5)

    assert len(received_messages) == 1
    assert received_messages[0].payload == test_payload

    # Fetch cached message
    cached_message = await redis_queue.fetch_cached_broadcast_message(cache_id)
    assert cached_message is not None
    assert cached_message == test_payload


async def test_done(redis_queue: RedisQueue):
    # Test message acknowledgment
    test_payload = {b"key": b"value"}

    # Send message
    await redis_queue.send(test_payload)

    # Consume and acknowledge message
    async for message in redis_queue.consume_queue():
        await redis_queue.done(message.msg_id)
        return
