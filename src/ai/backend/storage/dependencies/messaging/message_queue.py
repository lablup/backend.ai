from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.defs import REDIS_STREAM_DB, RedisRole
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.storage.context import EVENT_DISPATCHER_CONSUMER_GROUP


@dataclass
class MessageQueueInput:
    """Input required for the message queue setup."""

    redis_config: RedisConfig
    node_id: str


class MessageQueueProvider(
    NonMonitorableDependencyProvider[MessageQueueInput, AbstractMessageQueue]
):
    """Provider for the event message queue."""

    @property
    @override
    def stage_name(self) -> str:
        return "message-queue"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: MessageQueueInput) -> AsyncIterator[AbstractMessageQueue]:
        redis_profile_target = setup_input.redis_config.to_redis_profile_target()
        queue = await RedisQueue.create(
            redis_profile_target.profile_target(RedisRole.STREAM),
            RedisMQArgs(
                anycast_stream_key="events",
                broadcast_channel="events_all",
                consume_stream_keys=None,
                subscribe_channels={
                    "events_all",
                },
                group_name=EVENT_DISPATCHER_CONSUMER_GROUP,
                node_id=setup_input.node_id,
                db=REDIS_STREAM_DB,
            ),
        )
        yield queue
