from ai.backend.common.message_queue.hiredis_queue import HiRedisQueue
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.types import RedisProfileTarget

from .queue import AbstractMessageQueue


async def make_message_queue(
    redis_profile_target: RedisProfileTarget,
    mq_args: RedisMQArgs,
    use_experimental_redis_event_dispatcher: bool = False,
) -> AbstractMessageQueue:
    if use_experimental_redis_event_dispatcher:
        return HiRedisQueue.start(
            redis_profile_target,
            mq_args=mq_args,
        )
    return await RedisQueue.start(
        redis_profile_target,
        mq_args=mq_args,
    )
