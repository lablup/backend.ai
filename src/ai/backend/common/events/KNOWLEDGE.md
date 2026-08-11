---
name: event-handler-idempotency
type: constraints
description: why event handlers must be idempotent (ack only after all handlers complete, redelivery re-runs even the handlers that succeeded), discarding of events with no handler, absence of ordering guarantees, caller-context propagation, the event cache as compensation for lossy broadcast
scope: src/ai/backend/common/events
keywords: [EventDispatcher, idempotency, redelivery, ack, MessageMetadata, apply_context, EventFetcher, cache_domain, WithCachePropagator]
sources:
  - src/ai/backend/common/events/dispatcher.py
  - src/ai/backend/common/events/fetcher.py
  - src/ai/backend/common/events/hub/propagators/cache.py
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---

# Events — Knowledge

> Rules: `AGENTS.md` in the same directory. Delivery limits of the transport layer:
> [../message_queue/KNOWLEDGE.md](../message_queue/KNOWLEDGE.md).

## Why this package exists

It is the inter-component event layer that puts event types, a dispatcher, and a
cache on top of the message queue. This document holds the semantics handler
authors must uphold.

## Handlers must be idempotent

- An anycast message is acked only after **all** registered handlers have returned.
- If any handler fails, the message is redelivered and **all handlers run again, including the ones that already succeeded** — every handler must tolerate re-execution.
- That is why multi-handler anycast events are a risky shape — prefer a single consuming handler per anycast event.
- Handler failure does not stop the pump, and there are no ordering guarantees — neither across events nor across the handlers of one event.

## Unhandled events vanish silently

- An event with no registered handler is acked immediately and discarded.
- If a handler is registered on only some workers, the event is lost whenever another worker picks it up — register handlers unconditionally at startup.

## Caller context propagates along events

- `EventProducer` puts `current_request_id()`, `current_user()`, and `triggered_user()` into `MessageMetadata`, and the dispatcher re-injects them via `apply_context()` before running the handler.
- Tracing continues only if relays preserve the metadata — a handler that emits follow-up events without the metadata breaks the trace.

## The cache compensates for lossy broadcast

- Broadcast is fire-and-forget, so two domains (bgtask, session scheduler) also store the latest payload under a `cache_id` with a 5-minute TTL.
- SSE subscribers first replay the last cached event (closing the "subscribe after it happened" race) and use a polling safety net that re-queries the cache after every 30 seconds of silence.
- The cache keeps only the latest event per id — a reconnecting client gets a snapshot, not the intermediate events it missed.
