import asyncio
from collections.abc import AsyncGenerator, Iterator
from typing import NoReturn
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.message_queue.redis_queue.consumer import (
    RedisConsumer,
    RedisConsumerArgs,
)
from ai.backend.common.types import HostPortPair, RedisTarget

_NON_DEFAULT_DB = 7


async def _block_forever(*args: object, **kwargs: object) -> NoReturn:
    await asyncio.Future()
    raise AssertionError("unreachable")


class TestRedisConsumerDB:
    @pytest.fixture
    def stream_client_create(self) -> Iterator[AsyncMock]:
        client = MagicMock()
        client.make_consumer_group = AsyncMock()
        client.read_consumer_group = AsyncMock(side_effect=_block_forever)
        client.auto_claim_stream_message = AsyncMock(side_effect=_block_forever)
        client.close = AsyncMock()
        with patch(
            "ai.backend.common.message_queue.redis_queue.consumer.ValkeyStreamClient.create",
            new=AsyncMock(return_value=client),
        ) as create:
            yield create

    @pytest.fixture
    async def consumer(
        self, stream_client_create: AsyncMock
    ) -> AsyncGenerator[RedisConsumer, None]:
        consumer = await RedisConsumer.create(
            RedisTarget(addr=HostPortPair("127.0.0.1", 6379)),
            RedisConsumerArgs(
                stream_keys={"test-stream"},
                group_name="test-group",
                node_id="test-node",
                db=_NON_DEFAULT_DB,
            ),
        )
        yield consumer
        await consumer.close()

    async def test_reader_client_uses_configured_db(
        self, consumer: RedisConsumer, stream_client_create: AsyncMock
    ) -> None:
        async with asyncio.timeout(5):
            while stream_client_create.await_count < 2:
                await asyncio.sleep(0)

        assert [call.kwargs["db_id"] for call in stream_client_create.await_args_list] == [
            _NON_DEFAULT_DB,
            _NON_DEFAULT_DB,
        ]
