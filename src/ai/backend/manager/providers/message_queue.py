from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING

from ai.backend.common.defs import REDIS_STREAM_DB, RedisRole
from ai.backend.common.message_queue.hiredis_queue import HiRedisQueue
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue

if TYPE_CHECKING:
    from ..api.context import RootContext


async def _make_message_queue(
    root_ctx: RootContext,
) -> AbstractMessageQueue:
    from ..server import EVENT_DISPATCHER_CONSUMER_GROUP

    redis_profile_target = root_ctx.config_provider.config.redis.to_redis_profile_target()
    stream_redis_target = redis_profile_target.profile_target(RedisRole.STREAM)
    node_id = root_ctx.config_provider.config.manager.id
    args = RedisMQArgs(
        anycast_stream_key="events",
        broadcast_channel="events_all",
        consume_stream_keys={
            "events",
        },
        subscribe_channels={
            "events_all",
        },
        group_name=EVENT_DISPATCHER_CONSUMER_GROUP,
        node_id=node_id,
        db=REDIS_STREAM_DB,
    )
    if root_ctx.config_provider.config.manager.use_experimental_redis_event_dispatcher:
        return HiRedisQueue(
            stream_redis_target,
            args,
        )
    return await RedisQueue.create(
        stream_redis_target,
        args,
    )


@actxmgr
async def message_queue_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    root_ctx.message_queue = await _make_message_queue(root_ctx)
    yield
    await root_ctx.message_queue.close()
