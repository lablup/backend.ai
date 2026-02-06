"""GraphQL types for session management."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from typing import Any, Self
from uuid import UUID

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID
from strawberry.scalars import JSON

from ai.backend.manager.api.gql.base import OrderDirection
from ai.backend.manager.api.gql.common.types import (
    SchedulerInfoGQL,
    SessionResultGQL,
    SessionTypesGQL,
    VFolderMountGQL,
)
from ai.backend.manager.api.gql.fair_share.types.common import ResourceSlotGQL
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.data.session.types import SessionInfo, SessionStatus
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder

SessionStatusGQL = strawberry.enum(
    SessionStatus, name="SessionStatus", description="Added in 26.1.0"
)


# ========== Order and Filter Types ==========


@strawberry.enum(
    name="SessionOrderField",
    description="Added in 26.1.0. Fields available for ordering sessions.",
)
class SessionOrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    ID = "id"
    NAME = "name"


@strawberry.input(
    name="SessionStatusFilter", description="Added in 26.1.0. Filter for session status."
)
class SessionStatusFilterGQL:
    in_: list[SessionStatusGQL] | None = strawberry.field(name="in", default=None)
    not_in: list[SessionStatusGQL] | None = None

    def build_condition(self) -> QueryCondition | None:
        raise NotImplementedError


@strawberry.input(
    name="SessionFilter", description="Added in 26.1.0. Filter criteria for querying sessions."
)
class SessionFilterGQL(GQLFilter):
    id: UUID | None = None
    status: SessionStatusFilterGQL | None = None
    name: str | None = None
    domain_name: str | None = None
    group_id: UUID | None = None
    user_uuid: UUID | None = None

    def build_conditions(self) -> list[QueryCondition]:
        raise NotImplementedError


@strawberry.input(
    name="SessionOrderBy", description="Added in 26.1.0. Ordering specification for sessions."
)
class SessionOrderByGQL(GQLOrderBy):
    field: SessionOrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC

    def to_query_order(self) -> QueryOrder:
        raise NotImplementedError


# ========== Session Info Sub-Types ==========


@strawberry.type(
    name="SessionIdentityInfo",
    description="Added in 26.1.0. Basic identity information for a session.",
)
class SessionIdentityInfoGQL:
    id: ID = strawberry.field(description="Unique identifier of the session.")
    creation_id: str = strawberry.field(
        description="Client-provided creation ID for idempotent session creation."
    )
    name: str = strawberry.field(description="Human-readable name of the session.")
    session_type: SessionTypesGQL = strawberry.field(
        description="Type of the session (interactive, batch, inference)."
    )
    priority: int = strawberry.field(description="Scheduling priority of the session.")


@strawberry.type(
    name="SessionMetadataInfo",
    description="Added in 26.1.0. Metadata information for a session.",
)
class SessionMetadataInfoGQL:
    name: str = strawberry.field(description="Human-readable name of the session.")
    domain_name: str = strawberry.field(description="Domain to which this session belongs.")
    group_id: UUID = strawberry.field(description="Group/project ID that owns this session.")
    user_uuid: UUID = strawberry.field(description="User UUID who created this session.")
    access_key: str = strawberry.field(description="Access key used to create this session.")
    session_type: SessionTypesGQL = strawberry.field(
        description="Type of the session (interactive, batch, inference)."
    )
    priority: int = strawberry.field(description="Scheduling priority of the session.")
    created_at: datetime | None = strawberry.field(
        description="Timestamp when the session was created."
    )
    tag: str | None = strawberry.field(description="Optional user-provided tag for the session.")


@strawberry.type(
    name="SessionResourceInfo",
    description="Added in 26.1.0. Resource allocation information for a session.",
)
class SessionResourceInfoGQL:
    cluster_mode: str = strawberry.field(
        description="Cluster mode for distributed sessions (single-node, multi-node)."
    )
    cluster_size: int = strawberry.field(description="Number of nodes in the cluster.")
    occupying_slots: ResourceSlotGQL = strawberry.field(
        description="Currently occupied resource slots."
    )
    requested_slots: ResourceSlotGQL = strawberry.field(
        description="Originally requested resource slots."
    )
    scaling_group_name: str | None = strawberry.field(
        description="Name of the scaling group where the session is running."
    )
    target_sgroup_names: list[str] | None = strawberry.field(
        description="Target scaling group names for scheduling."
    )
    agent_ids: list[str] | None = strawberry.field(
        description="IDs of agents running the session's kernels."
    )


@strawberry.type(
    name="SessionImageInfo",
    description="Added in 26.1.0. Container image information for a session.",
)
class SessionImageInfoGQL:
    images: list[str] | None = strawberry.field(
        description="List of container image references used by the session."
    )
    tag: str | None = strawberry.field(description="Image tag if specified.")


@strawberry.type(
    name="SessionMountInfo",
    description="Added in 26.1.0. Virtual folder mount information for a session.",
)
class SessionMountInfoGQL:
    vfolder_mounts: list[VFolderMountGQL] | None = strawberry.field(
        description="List of virtual folders mounted to this session."
    )


@strawberry.type(
    name="SessionExecutionInfo",
    description="Added in 26.1.0. Execution configuration for a session.",
)
class SessionExecutionInfoGQL:
    environ: JSON | None = strawberry.field(
        description="Environment variables set for the session."
    )
    bootstrap_script: str | None = strawberry.field(
        description="Bootstrap script executed at session start."
    )
    startup_command: str | None = strawberry.field(
        description="Startup command executed after bootstrap."
    )
    use_host_network: bool = strawberry.field(
        description="Whether the session uses host network mode."
    )
    callback_url: str | None = strawberry.field(
        description="URL to call back when session status changes."
    )


@strawberry.type(
    name="SessionStatusDataContainer",
    description="Added in 26.1.0. Container for session status data.",
)
class SessionStatusDataContainerGQL:
    scheduler: SchedulerInfoGQL | None = strawberry.field(
        description="Scheduler-related status information."
    )
    raw: JSON | None = strawberry.field(description="Raw status data as JSON.")

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> SessionStatusDataContainerGQL | None:
        """Convert status_data mapping to GraphQL type."""
        raise NotImplementedError


@strawberry.type(
    name="SessionStatusHistoryEntry",
    description="Added in 26.1.0. A single entry in session status history.",
)
class SessionStatusHistoryEntryGQL:
    status: str = strawberry.field(description="The status value.")
    timestamp: datetime = strawberry.field(description="When this status was recorded.")


@strawberry.type(
    name="SessionStatusHistory",
    description="Added in 26.1.0. History of session status transitions.",
)
class SessionStatusHistoryGQL:
    entries: list[SessionStatusHistoryEntryGQL] = strawberry.field(
        description="List of status history entries."
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> SessionStatusHistoryGQL | None:
        """Convert status_history mapping to GraphQL type."""
        raise NotImplementedError


@strawberry.type(
    name="SessionLifecycleInfo",
    description="Added in 26.1.0. Lifecycle status and timestamps for a session.",
)
class SessionLifecycleInfoGQL:
    status: SessionStatusGQL = strawberry.field(description="Current status of the session.")
    result: SessionResultGQL = strawberry.field(
        description="Result of the session execution (success, failure, etc.)."
    )
    created_at: datetime | None = strawberry.field(
        description="Timestamp when the session was created."
    )
    terminated_at: datetime | None = strawberry.field(
        description="Timestamp when the session was terminated. Null if still active."
    )
    starts_at: datetime | None = strawberry.field(
        description="Scheduled start time for the session, if applicable."
    )
    status_changed: datetime | None = strawberry.field(
        description="Timestamp when the status was last changed."
    )
    batch_timeout: int | None = strawberry.field(
        description="Timeout in seconds for batch sessions."
    )
    status_info: str | None = strawberry.field(
        description="Additional information about the current status."
    )
    status_data: SessionStatusDataContainerGQL | None = strawberry.field(
        description="Structured status data including scheduler information."
    )
    status_history: SessionStatusHistoryGQL | None = strawberry.field(
        description="History of status transitions with timestamps."
    )


@strawberry.type(
    name="SessionStatEntry",
    description="Added in 26.1.0. A single statistic entry for session metrics.",
)
class SessionStatEntryGQL:
    name: str = strawberry.field(description="Name of the statistic.")
    current: str = strawberry.field(description="Current value.")
    capacity: str | None = strawberry.field(description="Maximum capacity if applicable.")
    unit_hint: str | None = strawberry.field(description="Unit hint for display.")


@strawberry.type(
    name="SessionStat",
    description="Added in 26.1.0. Collection of session statistics.",
)
class SessionStatGQL:
    entries: list[SessionStatEntryGQL] = strawberry.field(description="List of statistic entries.")

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> SessionStatGQL | None:
        """Convert last_stat mapping to GraphQL type."""
        raise NotImplementedError


@strawberry.type(
    name="SessionMetricsInfo",
    description="Added in 26.1.0. Metrics and statistics for a session.",
)
class SessionMetricsInfoGQL:
    num_queries: int = strawberry.field(
        description="The number of queries/executions performed in this session."
    )
    last_stat: SessionStatGQL | None = strawberry.field(
        description="The last collected statistics for this session."
    )


@strawberry.type(
    name="SessionNetworkInfo",
    description="Added in 26.1.0. Network configuration for a session.",
)
class SessionNetworkInfoGQL:
    network_type: str | None = strawberry.field(description="Type of network used by the session.")
    network_id: str | None = strawberry.field(description="ID of the network if applicable.")


# ========== Main Session Type ==========


@strawberry.type(
    name="SessionV2",
    description="Added in 26.1.0. Represents a compute session in Backend.AI.",
)
class SessionV2GQL(Node):
    """Session type representing a compute session."""

    id: NodeID[str]

    identity: SessionIdentityInfoGQL = strawberry.field(
        description="Basic identity information for the session."
    )
    metadata: SessionMetadataInfoGQL = strawberry.field(
        description="Metadata including domain, group, and user information."
    )
    resource: SessionResourceInfoGQL = strawberry.field(
        description="Resource allocation and cluster information."
    )
    image: SessionImageInfoGQL = strawberry.field(description="Container image information.")
    mounts: SessionMountInfoGQL = strawberry.field(description="Virtual folder mounts information.")
    execution: SessionExecutionInfoGQL = strawberry.field(
        description="Execution configuration (environment, scripts)."
    )
    lifecycle: SessionLifecycleInfoGQL = strawberry.field(
        description="Lifecycle status and timestamps."
    )
    metrics: SessionMetricsInfoGQL = strawberry.field(
        description="Execution metrics and statistics."
    )
    network: SessionNetworkInfoGQL = strawberry.field(description="Network configuration.")

    @classmethod
    def from_session_info(cls, session_info: SessionInfo) -> Self:
        """Create SessionV2GQL from SessionInfo dataclass."""
        raise NotImplementedError


# ========== Connection Types ==========


SessionEdgeGQL = Edge[SessionV2GQL]


@strawberry.type(
    name="SessionConnectionV2",
    description="Added in 26.1.0. Connection type for paginated session results.",
)
class SessionConnectionV2GQL(Connection[SessionV2GQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
