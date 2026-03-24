from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncGenerator
from enum import StrEnum
from typing import TYPE_CHECKING

import strawberry
from strawberry import Info

from ai.backend.common.bgtask.types import BgtaskStatus
from ai.backend.common.dto.manager.v2.background_task import (
    BackgroundTaskEventPayloadNode,
    BgtaskEventTypeDTO,
)
from ai.backend.common.events.event_types.bgtask.broadcast import (
    BgtaskAlreadyDoneEvent,
    BgtaskCancelledEvent,
    BgtaskDoneEvent,
    BgtaskFailedEvent,
    BgtaskUpdatedEvent,
)
from ai.backend.common.events.hub.propagators.cache import WithCachePropagator
from ai.backend.common.events.types import EventCacheDomain, EventDomain
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_enum,
    gql_pydantic_type,
    gql_subscription,
)
from ai.backend.manager.errors.bgtask import InvalidBgtaskId

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.types import StrawberryGQLContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@gql_enum(BackendAIGQLMeta(added_version="24.3.0", description="Type of background task event"))
class BgtaskEventType(StrEnum):
    """Enum representing background task event types."""

    UPDATED = "UPDATED"
    DONE = "DONE"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="24.3.0",
        description="Background task event payload.",
    ),
    model=BackgroundTaskEventPayloadNode,
    name="BackgroundTaskEventPayload",
)
class BackgroundTaskEventPayloadGQL:
    """Unified payload for all background task events.

    Progress fields (current_progress, total_progress) are only populated for UPDATED events.
    """

    task_id: strawberry.ID
    event_type: BgtaskEventType
    message: str
    current_progress: float | None = None
    total_progress: float | None = None

    @classmethod
    def from_updated_event(cls, event: BgtaskUpdatedEvent) -> BackgroundTaskEventPayloadGQL:
        """Create payload from BgtaskUpdatedEvent."""
        dto = BackgroundTaskEventPayloadNode(
            task_id=str(event.task_id),
            event_type=BgtaskEventTypeDTO.UPDATED,
            message=event.message or "",
            current_progress=event.current_progress,
            total_progress=event.total_progress,
        )
        return cls.from_pydantic(dto)  # type: ignore[attr-defined, no-any-return]

    @classmethod
    def from_done_event(cls, event: BgtaskDoneEvent) -> BackgroundTaskEventPayloadGQL:
        """Create payload from BgtaskDoneEvent."""
        dto = BackgroundTaskEventPayloadNode(
            task_id=str(event.task_id),
            event_type=BgtaskEventTypeDTO.DONE,
            message=event.message or "",
        )
        return cls.from_pydantic(dto)  # type: ignore[attr-defined, no-any-return]

    @classmethod
    def from_cancelled_event(cls, event: BgtaskCancelledEvent) -> BackgroundTaskEventPayloadGQL:
        """Create payload from BgtaskCancelledEvent."""
        dto = BackgroundTaskEventPayloadNode(
            task_id=str(event.task_id),
            event_type=BgtaskEventTypeDTO.CANCELLED,
            message=event.message or "",
        )
        return cls.from_pydantic(dto)  # type: ignore[attr-defined, no-any-return]

    @classmethod
    def from_failed_event(cls, event: BgtaskFailedEvent) -> BackgroundTaskEventPayloadGQL:
        """Create payload from BgtaskFailedEvent."""
        dto = BackgroundTaskEventPayloadNode(
            task_id=str(event.task_id),
            event_type=BgtaskEventTypeDTO.FAILED,
            message=event.message or "",
        )
        return cls.from_pydantic(dto)  # type: ignore[attr-defined, no-any-return]

    @classmethod
    def from_already_done_event(
        cls, event: BgtaskAlreadyDoneEvent
    ) -> BackgroundTaskEventPayloadGQL:
        """Create payload from BgtaskAlreadyDoneEvent based on its status."""
        match event.task_status:
            case BgtaskStatus.DONE | BgtaskStatus.PARTIAL_SUCCESS:
                event_type_dto = BgtaskEventTypeDTO.DONE
            case BgtaskStatus.CANCELLED:
                event_type_dto = BgtaskEventTypeDTO.CANCELLED
            case BgtaskStatus.FAILED:
                event_type_dto = BgtaskEventTypeDTO.FAILED
            case _:
                log.warning("Unknown task status in BgtaskAlreadyDoneEvent: {}", event.task_status)
                event_type_dto = BgtaskEventTypeDTO.FAILED

        dto = BackgroundTaskEventPayloadNode(
            task_id=str(event.task_id),
            event_type=event_type_dto,
            message=event.message or "",
        )
        return cls.from_pydantic(dto)  # type: ignore[attr-defined, no-any-return]


@gql_subscription(  # type: ignore[misc]
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Subscribe to real-time events for a specific background task. "
            "Streams progress updates and completion events (done/cancelled/failed) "
            "for the task lifecycle."
        ),
    )
)
async def background_task_events(
    task_id: strawberry.ID,
    info: Info[StrawberryGQLContext],
) -> AsyncGenerator[BackgroundTaskEventPayloadGQL, None]:
    """Subscribe to background task events for a specific task.

    Streams events for a background task, including:
    - Progress updates (UPDATED events with current/total progress)
    - Completion events (DONE/CANCELLED/FAILED)

    The subscription automatically ends when a completion event is received.

    Args:
        task_id: The UUID of the background task to monitor
        info: GraphQL context containing event hub and other services

    Yields:
        BackgroundTaskEventPayloadGQL: Event payload for progress updates or completion
    """
    # Parse and validate task_id
    try:
        task_uuid = uuid.UUID(task_id)
    except (ValueError, AttributeError) as e:
        log.warning("Invalid task ID format: {}", task_id)
        raise InvalidBgtaskId(f"Invalid task ID format: {task_id}") from e

    event_hub = info.context.event_hub
    event_fetcher = info.context.event_fetcher
    propagator = WithCachePropagator(event_fetcher)

    try:
        # Register propagator with event hub
        event_hub.register_event_propagator(
            propagator, aliases=[(EventDomain.BGTASK, str(task_uuid))]
        )

        # Get cache ID for this task
        cache_id = EventCacheDomain.BGTASK.cache_id(str(task_uuid))
        # Stream events from propagator
        async for event in propagator.receive(cache_id):
            # Convert event to payload
            payload: BackgroundTaskEventPayloadGQL | None = None
            is_close_event = False

            if isinstance(event, BgtaskUpdatedEvent):
                payload = BackgroundTaskEventPayloadGQL.from_updated_event(event)
            elif isinstance(event, BgtaskDoneEvent):
                payload = BackgroundTaskEventPayloadGQL.from_done_event(event)
                is_close_event = True
            elif isinstance(event, BgtaskCancelledEvent):
                payload = BackgroundTaskEventPayloadGQL.from_cancelled_event(event)
                is_close_event = True
            elif isinstance(event, BgtaskFailedEvent):
                payload = BackgroundTaskEventPayloadGQL.from_failed_event(event)
                is_close_event = True
            elif isinstance(event, BgtaskAlreadyDoneEvent):
                payload = BackgroundTaskEventPayloadGQL.from_already_done_event(event)
                is_close_event = True
            else:
                log.warning(
                    "Unknown background task event type: {}",
                    type(event).__name__,
                )
                continue

            if payload is not None:
                yield payload

            # End subscription on close events
            if is_close_event:
                log.debug("Received close event: {}", event.event_name())
                break

    finally:
        # Unregister propagator when subscription ends
        event_hub.unregister_event_propagator(propagator.id())
