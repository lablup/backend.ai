import asyncio

import pytest

from ai.backend.common.message_queue.hiredis_queue import HiRedisQueue
from ai.backend.common.message_queue.queue import BroadcastChannel, MQMessage, QueueStream
from ai.backend.common.message_queue.redis_queue import RedisMQArgs
from ai.backend.common.redis_client import RedisConnection
from ai.backend.common.types import (
    RedisHelperConfig,
    RedisTarget,
)


@pytest.fixture
def queue_args():
    return RedisMQArgs(
        anycast_stream_key=QueueStream.EVENTS,
        broadcast_channel=BroadcastChannel.ALL,
        consume_stream_keys=[QueueStream.EVENTS],
        subscribe_channels=[BroadcastChannel.ALL],
        group_name="test-group",
        node_id="test-node",
    )


@pytest.fixture
async def redis_queue(redis_container, queue_args):
    redis_target = RedisTarget(
        addr=redis_container[1],
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


async def test_send_and_consume(redis_queue):
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


async def test_subscribe(redis_queue):
    # Test message subscription
    test_payload = {b"key": b"value", b"key2": b"value2"}

    # Create task to subscribe
    received_messages: list[MQMessage] = []

    async def subscriber():
        async for message in redis_queue.subscribe_queue():
            received_messages.append(message)
            if len(received_messages) >= 1:
                break

    subscriber_task = asyncio.create_task(subscriber())

    # Send message
    await redis_queue.send(test_payload)

    # Wait for message to be received
    await asyncio.wait_for(subscriber_task, timeout=5)

    assert len(received_messages) == 1
    assert received_messages[0].payload == test_payload


async def test_done(redis_queue):
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
                redis_queue._stream_key,
                redis_queue._group_name,
            ])
            assert pending[0] == 0
            break


async def test_close(redis_queue):
    # Test queue closing
    await redis_queue.close()
    assert redis_queue._closed
    await asyncio.sleep(0.1)  # Allow time for tasks to be cancelled
    # Verify tasks are cancelled
    assert redis_queue._auto_claim_loop_task.cancelled()
    assert redis_queue._read_messages_task.cancelled()
    assert redis_queue._read_broadcast_messages_task.cancelled()
