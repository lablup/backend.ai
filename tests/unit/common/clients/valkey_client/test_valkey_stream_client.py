from __future__ import annotations

import asyncio
import random

from ai.backend.common.clients.valkey_client.valkey_stream.client import (
    ValkeyStreamClient,
)


async def test_valkey_stream_anycast(test_valkey_stream: ValkeyStreamClient) -> None:
    test_stream = f"test-stream-{random.randint(1000, 9999)}"
    test_group = f"test-group-{random.randint(1000, 9999)}"
    await test_valkey_stream.make_consumer_group(test_stream, test_group)
    await test_valkey_stream.enqueue_stream_message(
        test_stream,
        {
            b"key1": b"value1",
            b"key2": b"value2",
        },
    )
    values = await test_valkey_stream.read_consumer_group(test_stream, test_group, "test-consumer")
    assert values is not None
    assert len(values) == 1
    assert values[0].payload == {
        b"key1": b"value1",
        b"key2": b"value2",
    }
    await test_valkey_stream.done_stream_message("test-stream", "test-group", values[0].msg_id)


async def test_valkey_stream_broadcast(test_valkey_stream: ValkeyStreamClient) -> None:
    await test_valkey_stream.broadcast(
        "test-broadcast",
        {
            "key1": "value1",
            "key2": "value2",
        },
    )
    values = await test_valkey_stream.receive_broadcast_message()
    assert values == {
        "key1": "value1",
        "key2": "value2",
    }


async def test_valkey_stream_broadcast_with_cache(test_valkey_stream: ValkeyStreamClient) -> None:
    cache_id = f"test-cache-{random.randint(1000, 9999)}"
    await test_valkey_stream.broadcast_with_cache(
        "test-broadcast",
        cache_id,
        {
            "key1": "value1",
            "key2": "value2",
        },
    )
    values = await test_valkey_stream.receive_broadcast_message()
    assert values == {
        "key1": "value1",
        "key2": "value2",
    }
    cached_values = await test_valkey_stream.fetch_cached_broadcast_message(cache_id)
    assert cached_values is not None, "Cached values should not be None"
    assert cached_values == {
        "key1": "value1",
        "key2": "value2",
    }, "Cached values should match the broadcasted values"


async def test_valkey_stream_auto_claim(test_valkey_stream: ValkeyStreamClient) -> None:
    test_stream = f"test-stream-{random.randint(1000, 9999)}"
    test_group = f"test-group-{random.randint(1000, 9999)}"

    await test_valkey_stream.make_consumer_group(test_stream, test_group)
    await test_valkey_stream.enqueue_stream_message(
        test_stream,
        {
            b"key1": b"value1",
            b"key2": b"value2",
        },
    )
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
    assert auto_claimed.messages[0].payload == {
        b"key1": b"value1",
        b"key2": b"value2",
    }
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
