---
name: message-queue-delivery-guarantees
type: constraints
description: exact delivery limits of the Redis stream anycast path (auto-claim, discard after retries, no DLQ, shallow stream trim), broadcast as a compromise used only for loss-tolerant cases, single-stream/channel topology
scope: src/ai/backend/common/message_queue
keywords: [RedisQueue, consumer-group, auto-claim, retry, XADD, trim, pub/sub, at-least-once, DLQ]
sources:
  - src/ai/backend/common/message_queue/redis_queue
  - src/ai/backend/common/clients/valkey_client/valkey_stream/client.py
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---

# Message Queue — Knowledge

> Rules: `AGENTS.md` in the same directory.

## Why this package exists

It is the delivery abstraction over Redis streams (anycast) and pub/sub
(broadcast). This document holds the exact limits of the delivery guarantees
consumers may assume.

## Topology: one stream, one channel, one group per component

- All components share a single anycast stream key (`"events"`) and a single broadcast channel (`"events_all"`), distinguished only by consumer group (`"manager"`, `"agent"`, `"storage-proxy"`, ...).
- Adding a stream/channel is a topology decision, not a local one.

## Anycast is at-least-once — only within a shallow buffer

- A consumer group reads, an auto-claim loop (every 60 seconds) re-claims messages idle for 5 minutes, and after 3 retries a message is **acked and discarded — there is no DLQ**.
- Retry is implemented as ack-the-old plus re-add — a redelivered message gets a new id at the tail of the stream, so it loses ordering, and the message id is not a dedup key.
- Every add trims the stream to about 128 entries — if producers outrun consumers, even un-acked entries can disappear. This is not durable delivery.
- Connection failures do not stop the loop (unbounded backoff capped at 30 seconds), and a vanished consumer group is recreated automatically.

## Broadcast is a loss-tolerant compromise

- Pure pub/sub — there is no ack path, so a subscriber that is down or mid-restart/reconnect misses messages permanently.
- This is a compromise, not a design goal: the premise is the applicability rule that broadcast is used **only for events whose loss is acceptable**.
- If "eventually observed" is required, compensate with the events layer's cache plus polling ([../events/KNOWLEDGE.md](../events/KNOWLEDGE.md)) — do not assume redelivery here.
