from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Final

from ai.backend.common.defs import REDIS_STREAM_DB, RedisRole
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.message_queue.hiredis_queue import HiRedisQueue
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.manager.config.unified import ManagerUnifiedConfig

EVENT_DISPATCHER_CONSUMER_GROUP: Final = "manager"


@dataclass
class MessageQueueInput:
    """Input required for message queue setup.

    Contains configuration for Redis connection.
    """

    config: ManagerUnifiedConfig


class MessageQueueDependency(
    NonMonitorableDependencyProvider[MessageQueueInput, AbstractMessageQueue]
):
    """Provides AbstractMessageQueue lifecycle management."""

    @property
    def stage_name(self) -> str:
        return "message-queue"

    @asynccontextmanager
    async def provide(self, setup_input: MessageQueueInput) -> AsyncIterator[AbstractMessageQueue]:
        """Initialize and provide the message queue.

        Creates a RedisQueue or HiRedisQueue based on the configuration flag.

        Args:
            setup_input: Input containing configuration for Redis connection

        Yields:
            Initialized AbstractMessageQueue
        """
        config = setup_input.config
        redis_profile_target = config.redis.to_redis_profile_target()
        stream_redis_target = redis_profile_target.profile_target(RedisRole.STREAM)
        node_id = config.manager.id
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
        if config.manager.use_experimental_redis_event_dispatcher:
            queue: AbstractMessageQueue = HiRedisQueue(
                stream_redis_target,
                args,
            )
        else:
            queue = await RedisQueue.create(
                stream_redis_target,
                args,
            )
        try:
            yield queue
        finally:
            await queue.close()
