from dataclasses import dataclass
from typing import override

from ai.backend.common.defs import REDIS_STREAM_DB, RedisRole
from ai.backend.common.message_queue.hiredis_queue import HiRedisQueue
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)
from ai.backend.common.types import RedisProfileTarget

from ...config import StorageProxyPrivilegedWorkerConfig
from ...defs import EVENT_DISPATCHER_CONSUMER_GROUP


@dataclass
class MessageQueueSpec:
    local_config: StorageProxyPrivilegedWorkerConfig
    redis_profile_target: RedisProfileTarget


class MessageQueueSpecGenerator(ArgsSpecGenerator[MessageQueueSpec]):
    pass


@dataclass
class MessageQueueResult:
    message_queue: AbstractMessageQueue


class MessageQueueProvisioner(Provisioner[MessageQueueSpec, MessageQueueResult]):
    @property
    @override
    def name(self) -> str:
        return "storage-worker-redis-config"

    @override
    async def setup(self, spec: MessageQueueSpec) -> MessageQueueResult:
        stream_redis_target = spec.redis_profile_target.profile_target(RedisRole.STREAM)
        node_id = spec.local_config.storage_proxy.node_id
        args = RedisMQArgs(
            anycast_stream_key="events",
            broadcast_channel="events_all",
            consume_stream_keys=None,
            subscribe_channels={
                "events_all",
            },
            group_name=EVENT_DISPATCHER_CONSUMER_GROUP,
            node_id=node_id,
            db=REDIS_STREAM_DB,
        )
        if spec.local_config.storage_proxy.use_experimental_redis_event_dispatcher:
            return MessageQueueResult(
                HiRedisQueue(
                    stream_redis_target,
                    args,
                )
            )
        else:
            mq = await RedisQueue.create(
                spec.redis_profile_target.profile_target(RedisRole.STREAM),
                args,
            )
            return MessageQueueResult(mq)

    @override
    async def teardown(self, resource: MessageQueueResult) -> None:
        pass


class MessageQueueStage(ProvisionStage[MessageQueueSpec, MessageQueueResult]):
    pass
