from __future__ import annotations

import logging
import uuid
from enum import StrEnum
from typing import TYPE_CHECKING, AsyncGenerator

import strawberry
from strawberry import Info

from ai.backend.common.events.event_types.session.broadcast import SchedulingBroadcastEvent
from ai.backend.common.events.hub.propagators.bypass import AsyncBypassPropagator
from ai.backend.common.events.types import EventDomain
from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.gql.base import to_global_id
from ai.backend.manager.errors.kernel import InvalidSessionId
from ai.backend.manager.models.gql_models.session import ComputeSessionNode

from .session import Session

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.types import StrawberryGQLContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@strawberry.enum(description="Status of session scheduling transitions")
class SchedulingStatus(StrEnum):
    """
    Enum representing session scheduling status transitions.
    Subset of SessionStatus focusing on scheduling-relevant states.
    """

    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    PREPARING = "PREPARING"
    PULLING = "PULLING"
    PREPARED = "PREPARED"
    CREATING = "CREATING"
    RUNNING = "RUNNING"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"


@strawberry.type(description="Added in 25.15.0. Scheduling event broadcast payload")
class SchedulingBroadcastEventPayload:
    """
    Payload for scheduling broadcast events.
    Represents a status transition during session scheduling.
    """

    _session_id: strawberry.Private[strawberry.ID]
    status_transition: SchedulingStatus
    reason: str

    @classmethod
    def from_event(cls, event: SchedulingBroadcastEvent) -> SchedulingBroadcastEventPayload:
        """Create payload from SchedulingBroadcastEvent."""
        # Parse status_transition string to SchedulingStatus enum
        try:
            status_enum = SchedulingStatus(event.status_transition)
        except KeyError:
            log.warning(f"Unknown status transition: {event.status_transition}")
            status_enum = SchedulingStatus.ERROR

        return cls(
            _session_id=strawberry.ID(str(event.session_id)),
            status_transition=status_enum,
            reason=event.reason,
        )

    @strawberry.field(
        description="The session ID associated with the replica. This can be null right after replica creation."
    )
    async def session(self, info: Info[StrawberryGQLContext]) -> "Session":
        session_global_id = to_global_id(
            ComputeSessionNode, self._session_id, is_target_graphene_object=True
        )
        return Session(id=strawberry.ID(session_global_id))


@strawberry.subscription(
    description="Subscribe to real-time scheduling events for a specific session. "
    "Streams status transition events during the session lifecycle "
    "(PENDING → SCHEDULED → PREPARING → RUNNING → TERMINATED). "
    "Added in 25.15.0."
)
async def scheduling_events_by_session(
    session_id: strawberry.ID,
    info: Info[StrawberryGQLContext],
) -> AsyncGenerator[SchedulingBroadcastEventPayload, None]:
    """
    Subscribe to scheduling events for a specific session.

    This subscription streams status transition events for a session during its lifecycle,
    such as PENDING -> SCHEDULED -> PREPARING -> RUNNING -> TERMINATED.

    Args:
        session_id: The UUID of the session to monitor
        info: GraphQL context containing user information and services

    Yields:
        SchedulingBroadcastEventPayload: Event payloads for each status transition

    Requires:
        - User must own the session or have admin/superadmin permissions
    """
    # Parse session_id
    try:
        session_uuid = SessionId(uuid.UUID(session_id))
    except (ValueError, AttributeError) as e:
        log.warning(f"Invalid session ID format: {session_id}")
        raise InvalidSessionId(f"Invalid session ID format: {session_id}") from e

    event_hub = info.context.event_hub
    propagator = AsyncBypassPropagator()
    try:
        event_hub.register_event_propagator(
            propagator, aliases=[(EventDomain.SESSION, str(session_uuid))]
        )

        # Stream events from propagator
        async for event in propagator.receive():
            if isinstance(event, SchedulingBroadcastEvent):
                payload = SchedulingBroadcastEventPayload.from_event(event)
                yield payload
    finally:
        # Unregister propagator when subscription ends
        event_hub.unregister_event_propagator(propagator.id())
