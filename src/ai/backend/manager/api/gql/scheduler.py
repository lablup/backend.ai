from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncGenerator
from enum import StrEnum

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.v2.scheduler import (
    DryRunKernelResourceInput,
    DryRunScheduleInput,
    DryRunSchedulePayload,
    KernelDryRunResultInfo,
    SchedulingBroadcastEventPayloadNode,
    SchedulingStatusDTO,
    UnschedulableReasonHintInfo,
)
from ai.backend.common.events.event_types.session.broadcast import SchedulingBroadcastEvent
from ai.backend.common.events.hub.propagators.bypass import AsyncBypassPropagator
from ai.backend.common.events.types import EventDomain
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.gql.common_types import (
    ResourceSlotEntryGQL,
    ResourceSlotEntryInputGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_enum,
    gql_field,
    gql_pydantic_input,
    gql_pydantic_type,
    gql_root_field,
    gql_subscription,
)
from ai.backend.manager.api.gql.session.types import SessionClusterModeGQL
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.errors.common import ServiceUnavailable
from ai.backend.manager.errors.kernel import InvalidSessionId

from .session_federation import Session

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
    async def session(self, info: Info[StrawberryGQLContext]) -> Session | None:
        # The federated ComputeSessionNode stub is a relay.Node; pass the inner id so
        # Strawberry re-encodes the same global ID the graphene subgraph expects.
        return Session(id=strawberry.ID(str(self.session_id)))


@gql_subscription(
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
        log.warning("Invalid session ID format: {}", session_id)
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
                    log.warning("Unknown status transition: {}", event.status_transition)
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


# ---------------------------------------------------------------------------
# Dry-run schedule — probe a resource group's admission for a session's
# kernels without provisioning. Powers the session-launcher live feedback,
# so the query stays lightweight.
# ---------------------------------------------------------------------------


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Per-kernel resource request for a scheduling dry-run. The image is "
            "optional when a resource-group default supplies it downstream."
        ),
    ),
    name="DryRunKernelResourceInput",
)
class DryRunKernelResourceInputGQL(PydanticInputMixin[DryRunKernelResourceInput]):
    image_id: strawberry.ID | None = None
    resources: list[ResourceSlotEntryInputGQL] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Dry-run a session's scheduling against a resource group without provisioning.",
    ),
    name="DryRunScheduleInput",
)
class DryRunScheduleInputGQL(PydanticInputMixin[DryRunScheduleInput]):
    kernels: list[DryRunKernelResourceInputGQL]
    cluster_mode: SessionClusterModeGQL
    resource_group_id: strawberry.ID


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "What the caller could change so an unschedulable kernel would fit. "
            "Present only when the kernel's dry-run did not succeed."
        ),
    ),
    model=UnschedulableReasonHintInfo,
    name="UnschedulableReasonHint",
)
class UnschedulableReasonHintGQL:
    required_reduction: list[ResourceSlotEntryGQL] | None
    required_container_reduction: int | None
    available_archs: list[str] | None


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Dry-run outcome for a single kernel. Results correspond positionally "
            "to the requested kernels."
        ),
    ),
    model=KernelDryRunResultInfo,
    name="KernelDryRunResult",
)
class KernelDryRunResultGQL:
    requested_slots: list[ResourceSlotEntryGQL]
    requested_architecture: str
    success: bool
    reason_hint: UnschedulableReasonHintGQL | None


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Result of a dry-run schedule request.",
    ),
    model=DryRunSchedulePayload,
    name="DryRunSchedulePayload",
)
class DryRunSchedulePayloadGQL:
    dry_run_results: list[KernelDryRunResultGQL]


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Dry-run a session's scheduling against a resource group without "
            "provisioning. Returns per-kernel admission outcomes and, for kernels "
            "that do not fit, hints on what to reduce."
        ),
    )
)  # type: ignore[misc]
async def dry_run_schedule(
    input: DryRunScheduleInputGQL,
    info: Info[StrawberryGQLContext],
) -> DryRunSchedulePayloadGQL | None:
    # Schema-only surface: the adapter wiring lands in a follow-up.
    raise ServiceUnavailable("Dry-run schedule is not yet available.")
