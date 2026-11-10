from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Final, override

from ai.backend.common.clients.valkey_client.sentinel_monitor.monitor_set import SentinelMonitorSet
from ai.backend.common.defs import REDIS_STREAM_DB, RedisRole
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
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
    sentinel_monitors: SentinelMonitorSet


class MessageQueueDependency(
    NonMonitorableDependencyProvider[MessageQueueInput, AbstractMessageQueue]
):
    """Provides AbstractMessageQueue lifecycle management."""

    @property
    @override
    def stage_name(self) -> str:
        return "message-queue"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: MessageQueueInput) -> AsyncIterator[AbstractMessageQueue]:
        """Initialize and provide the message queue.

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
        queue = await RedisQueue.create(
            stream_redis_target,
            args,
            setup_input.sentinel_monitors.monitor_for(stream_redis_target.to_valkey_target()),
        )
        try:
            yield queue
        finally:
            await queue.close()
