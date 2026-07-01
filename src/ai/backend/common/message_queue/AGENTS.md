# Message Queue

Abstraction over Redis streams (anycast) and pub/sub (broadcast). Prefer `RedisQueue` (`redis_queue/queue.py`); `hiredis_queue.py` is legacy.

## Interfaces (`abc/`)

- `AbstractAnycaster.anycast()` / `AbstractConsumer.consume_queue()` — point-to-point, exactly one consumer receives; reliable (consumer group + auto-claim).
- `AbstractBroadcaster.broadcast()` / `AbstractSubscriber.subscribe_queue()` — fan-out, fire-and-forget, no ack.

## Rules

- **Consumers must call `done(msg_id)` after handling** — otherwise the message is redelivered after the idle timeout, then discarded past max retries.
- Subscribers do not ack (broadcast may be lost by design).
- Anycast payload is `dict[bytes, bytes]`; broadcast payload is `dict[str, str]`. Do not mix.
- Configure only the streams/channels you use (`consume_stream_keys=None` / `subscribe_channels=None`) to avoid idle background loops.
- Always `await close()` the queue/components to avoid connection and task leaks.

## Types (`types.py`)

`MQMessage` (anycast), `BroadcastMessage` (broadcast), `MessagePayload` (high-level, used by the events system). When relaying, preserve `MessageMetadata` (request_id/user) via `apply_context()`.
