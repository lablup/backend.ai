# Events

Event classes live in `event_types/{domain}/{anycast|broadcast}.py`; base types and the dispatcher are in this package.

## Define an event

- Subclass `AbstractAnycastEvent` (one consumer) or `AbstractBroadcastEvent` (all subscribers) from `types.py`. The base class — not a flag — decides the delivery pattern.
- An event is a Pydantic model: declare its body as annotated fields, and construct it by keyword. Do NOT use `@dataclass`.
- Implement `event_name()` (unique snake_case), `event_domain()` (an `EventDomain` value), and `serialize()` / `deserialize()`.
- **`serialize()` and `deserialize()` must use the same tuple order** — a mismatch silently swaps fields.
- Do NOT write `to_message()` / `from_message()`. `AbstractEvent` derives both from the model's fields, so the body an event carries is its field set and nothing else. Override them only to refuse — an event that must never cross the queue raises there, as `BgtaskAlreadyDoneEvent` does.
- If the domain is new, add it to `EventDomain` in `types.py` first.
- Broadcast events auto-register by `event_name()` via `__init_subclass__`; a duplicate name raises at import. Anycast events are not registered — they are referenced directly at `consume()`.

## Register a handler

- Anycast: `dispatcher.consume(EventCls, context, callback)`.
- Broadcast: `dispatcher.subscribe(EventCls, context, callback)`.
- Callback signature: `async (context, agent_id, event) -> None`.

## Optional

- `user_event()` — surface the event on the EventStreaming API.
- `cache_domain()` (broadcast only) — make the event cacheable/fetchable via `fetcher.py`.
