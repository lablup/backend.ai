from collections.abc import Sequence
from dataclasses import dataclass

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.session.anycast import (
    SessionStatusTransitionAnycastEvent,
)
from ai.backend.common.events.event_types.session.broadcast import SchedulingBroadcastEvent
from ai.backend.common.types import SessionId
from ai.backend.manager.data.session.types import SessionStatus


@dataclass(frozen=True)
class SessionStatusTransition:
    session_id: SessionId
    to_status: SessionStatus
    reason: str
    #: When equal to ``to_status``, the write is a re-run of the same phase and is not anycast.
    from_status: SessionStatus | None = None
    #: ``None`` skips the broadcast only; ``SchedulingBroadcastEvent`` requires a creation id.
    creation_id: str | None = ""


async def produce_session_status_transition_events(
    event_producer: EventProducer,
    transitions: Sequence[SessionStatusTransition],
    *,
    broadcast: bool = True,
) -> None:
    """Anycast each transition for the session callback, and broadcast it for SSE and GQL subscriptions."""
    for transition in transitions:
        if transition.from_status == transition.to_status:
            continue
        await event_producer.anycast_event(
            SessionStatusTransitionAnycastEvent(
                session_id=transition.session_id,
                status=str(transition.to_status),
                reason=transition.reason,
            )
        )
    if not broadcast:
        return
    await event_producer.broadcast_events_batch([
        SchedulingBroadcastEvent(
            session_id=transition.session_id,
            creation_id=transition.creation_id,
            status_transition=str(transition.to_status),
            reason=transition.reason,
        )
        for transition in transitions
        if transition.creation_id is not None
    ])
