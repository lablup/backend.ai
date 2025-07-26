from dataclasses import dataclass
from typing import override

from ai.backend.common.defs import REDIS_STREAM_DB, RedisRole
from ai.backend.common.message_queue.hiredis_queue import HiRedisQueue
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.stage.types import Provisioner
from ai.backend.common.types import RedisProfileTarget

EVENT_DISPATCHER_CONSUMER_GROUP = "manager"


@dataclass
class MessageQueueSpec:
    redis_profile_target: RedisProfileTarget
    node_id: str
    use_experimental_redis_event_dispatcher: bool


class MessageQueueProvisioner(Provisioner):
    @property
    @override
    def name(self) -> str:
        return "message-queue-provisioner"

    @override
    async def setup(self, spec: MessageQueueSpec) -> AbstractMessageQueue:
        stream_redis_target = spec.redis_profile_target.profile_target(RedisRole.STREAM)
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
            node_id=spec.node_id,
            db=REDIS_STREAM_DB,
        )
        if spec.use_experimental_redis_event_dispatcher:
            return HiRedisQueue(
                stream_redis_target,
                args,
            )
        return await RedisQueue.create(
            stream_redis_target,
            args,
        )

    @override
    async def teardown(self, resource: AbstractMessageQueue) -> None:
        await resource.close()
