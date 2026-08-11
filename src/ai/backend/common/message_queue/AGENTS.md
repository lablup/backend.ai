# Message Queue

Abstraction over Redis streams (anycast) and pub/sub (broadcast). Prefer `RedisQueue` (`redis_queue/queue.py`); `hiredis_queue.py` is legacy.

## Interfaces (`abc/`)

- `AbstractAnycaster.anycast()` / `AbstractConsumer.consume_queue()` — point-to-point, exactly one consumer receives; reliable (consumer group + auto-claim).
- `AbstractBroadcaster.broadcast()` / `AbstractSubscriber.subscribe_queue()` — fan-out, fire-and-forget, no ack.

## Rules

- **Consumers must call `done(msg_id)` after handling** — otherwise the message is redelivered after the idle timeout, then discarded past max retries.
- Subscribers do not ack (broadcast may be lost by design).
- Anycast carries `AnycastPayload`, broadcast carries `BroadcastPayload`. Do not mix, and do not hand-build the wire mapping — the payload models own the encoding.
- Decode received messages with `from_stream_fields()` / `from_json()`; they raise `InvalidMessagePayloadError` instead of failing later at field access.
- Configure only the streams/channels you use (`consume_stream_keys=None` / `subscribe_channels=None`) to avoid idle background loops.
- Always `await close()` the queue/components to avoid connection and task leaks.

## Types

| Module | Holds |
|--------|-------|
| `payload.py` | The payloads: `MessagePayload` base (`name`, `source`, `body`, `metadata`), `AnycastPayload` (adds `retry_count` + stream-field codec), `BroadcastPayload` (adds the JSON codec), `CachedBroadcastPayload` (a broadcast payload plus its `cache_id`, for `broadcast_batch()`) |
| `message.py` | What a consumer receives: `MQMessage` (anycast payload + the stream entry id needed to ack it, `retry()`) and `MessageId` |
| `types.py` | `MessageMetadata` — when relaying, preserve it (request_id/user) via `apply_context()` |
