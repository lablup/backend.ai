from dataclasses import dataclass
from typing import override

from ai.backend.common.defs import REDIS_STREAM_DB, RedisRole
from ai.backend.common.message_queue.hiredis_queue import HiRedisQueue
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.stage.types import Provisioner, ProvisionStage, SpecGenerator
from ai.backend.common.types import RedisProfileTarget
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.setup.provisioners.redis import RedisStage

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


class MessageQueueSpecGenerator(SpecGenerator[MessageQueueSpec]):
    def __init__(self, redis_stage: RedisStage, config: ManagerUnifiedConfig):
        self.redis_stage = redis_stage
        self.config = config

    @override
    async def wait_for_spec(self) -> MessageQueueSpec:
        redis_clients = await self.redis_stage.wait_for_resource()
        return MessageQueueSpec(
            redis_profile_target=redis_clients.redis_profile_target,
            node_id=self.config.manager.id,
            use_experimental_redis_event_dispatcher=self.config.manager.use_experimental_redis_event_dispatcher,
        )


# Type alias for MessageQueue stage
MessageQueueStage = ProvisionStage[MessageQueueSpec, AbstractMessageQueue]
