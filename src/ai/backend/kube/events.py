from __future__ import annotations

from ai.backend.common.defs import REDIS_STREAM_DB
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.message_queue.redis_queue.queue import RedisMQArgs, RedisQueue
from ai.backend.common.types import AgentId, HostPortPair, RedisTarget


async def make_event_producer(
    source: str, node_id: str, valkey_addr: str, valkey_password: str | None
) -> EventProducer:
    """A producer on the Manager's event stream. `source` is the cluster's agent id."""
    host, _, port = valkey_addr.rpartition(":")
    target = RedisTarget(addr=HostPortPair(host, int(port)), password=valkey_password)
    queue = await RedisQueue.create(
        target,
        RedisMQArgs(
            anycast_stream_key="events",
            broadcast_channel="events_all",
            consume_stream_keys=None,
            subscribe_channels=None,
            group_name="kube-cluster",
            node_id=node_id,
            db=REDIS_STREAM_DB,
        ),
    )
    return EventProducer(queue, source=AgentId(source))
