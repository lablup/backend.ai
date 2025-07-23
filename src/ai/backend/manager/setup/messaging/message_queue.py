from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.defs import REDIS_STREAM_DB
from ai.backend.common.message_queue.hiredis_queue import HiRedisQueue
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.stage.types import Provisioner
from ai.backend.common.types import RedisProfileTarget, RedisRole
from ai.backend.manager.config.unified import ManagerUnifiedConfig


EVENT_DISPATCHER_CONSUMER_GROUP = "manager"


@dataclass
class MessageQueueSpec:
    config: ManagerUnifiedConfig


class MessageQueueProvisioner(Provisioner[MessageQueueSpec, AbstractMessageQueue]):
    @property
    def name(self) -> str:
        return "message_queue"

    async def setup(self, spec: MessageQueueSpec) -> AbstractMessageQueue:
        redis_profile_target = RedisProfileTarget.from_dict(
            spec.config.redis.model_dump()
        )
        stream_redis_target = redis_profile_target.profile_target(RedisRole.STREAM)
        node_id = spec.config.manager.id
        
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
        
        if spec.config.manager.use_experimental_redis_event_dispatcher:
            return HiRedisQueue(
                stream_redis_target,
                args,
            )
        
        return await RedisQueue.create(
            stream_redis_target,
            args,
        )

    async def teardown(self, resource: AbstractMessageQueue) -> None:
        await resource.close()