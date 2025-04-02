import asyncio

import pytest

from ai.backend.common import redis_helper
from ai.backend.common.message_queue.queue import MQMessage
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.types import (
    RedisConfig,
    RedisHelperConfig,
)


@pytest.fixture
async def redis_conn(redis_container):
    # Configure test Redis connection
    conn = redis_helper.get_redis_object(
        RedisConfig(
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
def queue_args():
    return RedisMQArgs(
        stream_key="test-stream",
        group_name="test-group",
        node_id="test-node",
    )


@pytest.fixture
async def redis_queue(redis_conn, queue_args):
    # Create consumer group if not exists
    try:
        await redis_conn.client.xgroup_create(
            queue_args.stream_key, queue_args.group_name, mkstream=True
        )
    except Exception:
        # Group may already exist
        pass

    queue = RedisQueue(redis_conn, queue_args)
    yield queue
    await queue.close()


async def test_send_and_consume(redis_queue):
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

    # Send message
    await redis_queue.send(test_payload)

    # Consume and acknowledge message
    async for message in redis_queue.consume_queue():
        await redis_queue.done(message.msg_id)
        # Message should be acknowledged in Redis
        pending = await redis_queue._conn.client.xpending(
            redis_queue._stream_key, redis_queue._group_name
        )
        assert pending["pending"] == 0
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
