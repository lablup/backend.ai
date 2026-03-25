from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncGenerator
from enum import StrEnum
from typing import TYPE_CHECKING

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.v2.scheduler import (
    SchedulingBroadcastEventPayloadNode,
    SchedulingStatusDTO,
)
from ai.backend.common.events.event_types.session.broadcast import SchedulingBroadcastEvent
from ai.backend.common.events.hub.propagators.bypass import AsyncBypassPropagator
from ai.backend.common.events.types import EventDomain
from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.gql.base import to_global_id
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_enum,
    gql_field,
    gql_pydantic_type,
    gql_subscription,
)
from ai.backend.manager.api.gql_legacy.session import ComputeSessionNode
from ai.backend.manager.errors.kernel import InvalidSessionId

from .session_federation import Session

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.types import StrawberryGQLContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@gql_enum(
    BackendAIGQLMeta(added_version="24.3.0", description="Status of session scheduling transitions")
)
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


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.15.0",
        description="Scheduling event broadcast payload.",
    ),
    model=SchedulingBroadcastEventPayloadNode,
    name="SchedulingBroadcastEventPayload",
)
class SchedulingBroadcastEventPayloadGQL:
    """Payload for scheduling broadcast events.

    Represents a status transition during session scheduling.
    """

    session_id: strawberry.ID
    status_transition: SchedulingStatus
    reason: str

    @gql_field(
        description="The session ID associated with the replica. This can be null right after replica creation."
    )  # type: ignore[misc]
    async def session(self, info: Info[StrawberryGQLContext]) -> Session:
        session_global_id = to_global_id(
            ComputeSessionNode, self.session_id, is_target_graphene_object=True
        )
        return Session(id=strawberry.ID(session_global_id))


@gql_subscription(  # type: ignore[misc]
    BackendAIGQLMeta(
        added_version="25.15.0",
        description=(
            "Subscribe to real-time scheduling events for a specific session. "
            "Streams status transition events during the session lifecycle "
            "(PENDING → SCHEDULED → PREPARING → RUNNING → TERMINATED)."
        ),
    )
)
async def scheduling_events_by_session(
    session_id: strawberry.ID,
    info: Info[StrawberryGQLContext],
) -> AsyncGenerator[SchedulingBroadcastEventPayloadGQL, None]:
    """Subscribe to scheduling events for a specific session.

    Streams status transition events for a session during its lifecycle,
    such as PENDING -> SCHEDULED -> PREPARING -> RUNNING -> TERMINATED.

    Args:
        session_id: The UUID of the session to monitor
        info: GraphQL context containing user information and services

    Yields:
        SchedulingBroadcastEventPayloadGQL: Event payloads for each status transition

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
                try:
                    status_dto = SchedulingStatusDTO(event.status_transition)
                except ValueError:
                    log.warning(f"Unknown status transition: {event.status_transition}")
                    status_dto = SchedulingStatusDTO.ERROR
                dto = SchedulingBroadcastEventPayloadNode(
                    session_id=str(event.session_id),
                    status_transition=status_dto,
                    reason=event.reason,
                )
                yield SchedulingBroadcastEventPayloadGQL.from_pydantic(dto)  # type: ignore[attr-defined]
    finally:
        # Unregister propagator when subscription ends
        event_hub.unregister_event_propagator(propagator.id())
