from __future__ import annotations

import asyncio
import random

from ai.backend.common.clients.valkey_client.valkey_stream.client import (
    ValkeyStreamClient,
)
from ai.backend.common.message_queue.payload import AnycastMessagePayload, BroadcastMessagePayload
from ai.backend.common.message_queue.types import MessageName


def _anycast_payload() -> AnycastMessagePayload:
    return AnycastMessagePayload(name=MessageName("test-event"), source="i-test", payload="{}")


def _broadcast_payload() -> BroadcastMessagePayload:
    return BroadcastMessagePayload(name=MessageName("test-event"), source="i-test", payload="{}")


async def test_valkey_stream_anycast(test_valkey_stream: ValkeyStreamClient) -> None:
    test_stream = f"test-stream-{random.randint(1000, 9999)}"
    test_group = f"test-group-{random.randint(1000, 9999)}"
    payload = _anycast_payload()
    await test_valkey_stream.make_consumer_group(test_stream, test_group)
    await test_valkey_stream.enqueue_stream_message(test_stream, payload)
    values = await test_valkey_stream.read_consumer_group(test_stream, test_group, "test-consumer")
    assert values is not None
    assert len(values) == 1
    assert AnycastMessagePayload.from_stream_fields(values[0].payload) == payload
    await test_valkey_stream.done_stream_message("test-stream", "test-group", values[0].msg_id)


async def test_valkey_stream_broadcast(test_valkey_stream: ValkeyStreamClient) -> None:
    payload = _broadcast_payload()
    await test_valkey_stream.broadcast("test-broadcast", payload)
    received = await test_valkey_stream.receive_broadcast_message()
    assert received == payload


async def test_valkey_stream_broadcast_with_cache(test_valkey_stream: ValkeyStreamClient) -> None:
    cache_id = f"test-cache-{random.randint(1000, 9999)}"
    payload = _broadcast_payload()
    await test_valkey_stream.broadcast_with_cache("test-broadcast", cache_id, payload)
    received = await test_valkey_stream.receive_broadcast_message()
    assert received == payload
    cached = await test_valkey_stream.fetch_cached_broadcast_message(cache_id)
    assert cached is not None, "Cached message should not be None"
    assert cached == payload, "Cached message should match the broadcasted one"


async def test_valkey_stream_auto_claim(test_valkey_stream: ValkeyStreamClient) -> None:
    test_stream = f"test-stream-{random.randint(1000, 9999)}"
    test_group = f"test-group-{random.randint(1000, 9999)}"
    payload = _anycast_payload()

    await test_valkey_stream.make_consumer_group(test_stream, test_group)
    await test_valkey_stream.enqueue_stream_message(test_stream, payload)
    await test_valkey_stream.read_consumer_group(test_stream, test_group, "test-consumer")
    await asyncio.sleep(0.1)  # Ensure the message is available for auto claim
    # Auto claim the message
    auto_claimed = await test_valkey_stream.auto_claim_stream_message(
        test_stream,
        test_group,
        "test-consumer",
        "0-0",
        min_idle_timeout=0,  # Set to 0 for immediate auto claim
        count=1,
    )
    assert auto_claimed is not None, "Auto claim should return a result"
    assert len(auto_claimed.messages) == 1, "One message should be available for auto claim"
    assert AnycastMessagePayload.from_stream_fields(auto_claimed.messages[0].payload) == payload
    # Acknowledge the auto claimed message
    await test_valkey_stream.done_stream_message(
        test_stream, test_group, auto_claimed.messages[0].msg_id
    )

    auto_claimed = await test_valkey_stream.auto_claim_stream_message(
        test_stream,
        test_group,
        "test-consumer",
        "0-0",
        min_idle_timeout=0,  # Set to 0 for immediate auto claim
        count=1,
    )
    assert auto_claimed is not None, "Auto claim should return a result"
    assert len(auto_claimed.messages) == 0, (
        "No messages should be available for auto claim after acknowledging the previous one"
    )
