import asyncio
import random
from collections.abc import AsyncIterator

import pytest

from ai.backend.common.message_queue.hiredis_queue import HiRedisQueue
from ai.backend.common.message_queue.redis_queue import RedisMQArgs
from ai.backend.common.message_queue.types import BroadcastMessage, MQMessage
from ai.backend.common.redis_client import RedisConnection
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import (
    RedisHelperConfig,
    RedisTarget,
)


@pytest.fixture
def queue_args() -> RedisMQArgs:
    return RedisMQArgs(
        anycast_stream_key="test-stream",
        broadcast_channel="test-broadcast",
        consume_stream_keys={"test-stream"},
        subscribe_channels={"test-broadcast"},
        group_name="test-group",
        node_id="test-node",
        db=0,
    )


@pytest.fixture
async def redis_queue(redis_container, queue_args) -> AsyncIterator[HiRedisQueue]:
    hostport_pair: HostPortPairModel = redis_container[1]
    redis_target = RedisTarget(
        addr=hostport_pair.to_legacy(),
        redis_helper_config=RedisHelperConfig(
            socket_timeout=1.0,
            socket_connect_timeout=1.0,
            reconnect_poll_timeout=1.0,
            max_connections=10,
            connection_ready_timeout=1.0,
        ),
    )

    queue = HiRedisQueue(redis_target, queue_args)
    yield queue
    async with RedisConnection(redis_target, db=queue_args.db) as client:
        # Cleanup after tests
        await client.execute(["FLUSHDB"])
    await queue.close()


async def test_send_and_consume(redis_queue: HiRedisQueue) -> None:
    # Test message sending and consuming
    test_payload = {b"key": b"value", b"key2": b"value2"}

    await asyncio.sleep(0.1)
    # Send message
    await redis_queue.send(test_payload)

    # Consume message
    async for message in redis_queue.consume_queue():
        assert isinstance(message, MQMessage)
        assert message.payload == test_payload
        await redis_queue.done(message.msg_id)
        break


async def test_subscribe(redis_queue: HiRedisQueue) -> None:
    # Test message subscription
    test_payload = {"key": "value", "key2": "value2"}

    # Create task to subscribe
    received_messages: list[BroadcastMessage] = []

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


async def test_broadcast_with_cache(redis_queue: HiRedisQueue) -> None:
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


async def test_done(redis_queue: HiRedisQueue):
    # Test message acknowledgment
    test_payload = {b"key": b"value"}
    await asyncio.sleep(0.1)

    # Send message
    await redis_queue.send(test_payload)

    # Consume and acknowledge message
    async for message in redis_queue.consume_queue():
        print(message)
        await redis_queue.done(message.msg_id)
        # Message should be acknowledged in Redis
        async with RedisConnection(redis_queue._target, db=redis_queue._db) as client:
            pending = await client.execute([
                "XPENDING",
                redis_queue._anycast_stream_key,
                redis_queue._group_name,
            ])
            assert pending[0] == 0
            break


async def test_close(redis_queue: HiRedisQueue):
    # Test queue closing
    await redis_queue.close()
    assert redis_queue._closed
    await asyncio.sleep(0.1)  # Allow time for tasks to be cancelled
    # Verify tasks are cancelled
    for task in redis_queue._loop_tasks:
        assert task.done() or task.cancelled(), "Task should be cancelled after closing the queue"
