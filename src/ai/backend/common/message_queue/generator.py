from ai.backend.common import redis_helper
from ai.backend.common.defs import RedisRole
from ai.backend.common.message_queue.hiredis_queue import HiRedisQueue
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.types import RedisProfileTarget

from .queue import AbstractMessageQueue


async def make_message_queue(
    redis_profile_target: RedisProfileTarget,
    redis_role: RedisRole,
    mq_args: RedisMQArgs,
    use_experimental_redis_event_dispatcher: bool = False,
) -> AbstractMessageQueue:
    stream_redis_target = redis_profile_target.profile_target(redis_role)
    if use_experimental_redis_event_dispatcher:
        return HiRedisQueue(
            stream_redis_target,
            mq_args,
        )
    stream_redis = await redis_helper.create_valkey_client(
        stream_redis_target,
        name="event_producer.stream",
        db=redis_role.db_index,
    )
    return RedisQueue(stream_redis, mq_args)
