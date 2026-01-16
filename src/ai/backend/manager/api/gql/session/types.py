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

from ai.backend.common.types import SessionId
from ai.backend.manager.api.gql.base import OrderDirection
from ai.backend.manager.api.gql.common.types import (
    SchedulerInfoGQL,
    SchedulerPredicateGQL,
    SessionResultGQL,
    SessionTypesGQL,
    VFolderMountGQL,
)
from ai.backend.manager.api.gql.fair_share.types.common import ResourceSlotGQL
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.data.session.types import SessionInfo, SessionStatus
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.scheduler.options import SessionConditions, SessionOrders

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
        if self.in_:
            return SessionConditions.by_statuses(self.in_)
        if self.not_in:
            all_statuses = set(SessionStatus)
            allowed_statuses = all_statuses - set(self.not_in)
            return SessionConditions.by_statuses(list(allowed_statuses))
        return None


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
        conditions: list[QueryCondition] = []
        if self.id:
            conditions.append(SessionConditions.by_id(SessionId(self.id)))
        if self.status:
            condition = self.status.build_condition()
            if condition:
                conditions.append(condition)
        if self.name:
            conditions.append(SessionConditions.by_name(self.name))
        if self.domain_name:
            conditions.append(SessionConditions.by_domain_name(self.domain_name))
        if self.group_id:
            conditions.append(SessionConditions.by_group_id(self.group_id))
        if self.user_uuid:
            conditions.append(SessionConditions.by_user_uuid(self.user_uuid))
        return conditions


@strawberry.input(
    name="SessionOrderBy", description="Added in 26.1.0. Ordering specification for sessions."
)
class SessionOrderByGQL(GQLOrderBy):
    field: SessionOrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC

    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case SessionOrderFieldGQL.CREATED_AT:
                return SessionOrders.created_at(ascending)
            case SessionOrderFieldGQL.ID:
                return SessionOrders.id(ascending)
            case SessionOrderFieldGQL.NAME:
                return SessionOrders.name(ascending)


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
        if data is None:
            return None

        scheduler_info: SchedulerInfoGQL | None = None
        if scheduler_data := data.get("scheduler"):
            failed_predicates = None
            passed_predicates = None
            if fp := scheduler_data.get("failed_predicates"):
                failed_predicates = [
                    SchedulerPredicateGQL(name=p.get("name", ""), msg=p.get("msg")) for p in fp
                ]
            if pp := scheduler_data.get("passed_predicates"):
                passed_predicates = [
                    SchedulerPredicateGQL(name=p.get("name", ""), msg=p.get("msg")) for p in pp
                ]
            scheduler_info = SchedulerInfoGQL(
                retries=scheduler_data.get("retries"),
                last_try=scheduler_data.get("last_try"),
                msg=scheduler_data.get("msg"),
                failed_predicates=failed_predicates,
                passed_predicates=passed_predicates,
            )

        return cls(scheduler=scheduler_info, raw=data if data else None)


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
        if data is None:
            return None
        entries = []
        for status, timestamp_str in data.items():
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    entries.append(SessionStatusHistoryEntryGQL(status=status, timestamp=timestamp))
                except (ValueError, AttributeError):
                    pass
        return cls(entries=entries)


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
        if data is None:
            return None
        entries = []
        for name, value in data.items():
            if isinstance(value, dict):
                entries.append(
                    SessionStatEntryGQL(
                        name=name,
                        current=str(value.get("current", "")),
                        capacity=str(value.get("capacity")) if value.get("capacity") else None,
                        unit_hint=value.get("unit_hint"),
                    )
                )
        return cls(entries=entries)


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
        return cls(
            id=ID(str(session_info.identity.id)),
            identity=SessionIdentityInfoGQL(
                id=ID(str(session_info.identity.id)),
                creation_id=session_info.identity.creation_id,
                name=session_info.identity.name,
                session_type=SessionTypesGQL(session_info.identity.session_type),
                priority=session_info.identity.priority,
            ),
            metadata=SessionMetadataInfoGQL(
                name=session_info.metadata.name,
                domain_name=session_info.metadata.domain_name,
                group_id=session_info.metadata.group_id,
                user_uuid=session_info.metadata.user_uuid,
                access_key=session_info.metadata.access_key,
                session_type=SessionTypesGQL(session_info.metadata.session_type),
                priority=session_info.metadata.priority,
                created_at=session_info.metadata.created_at,
                tag=session_info.metadata.tag,
            ),
            resource=SessionResourceInfoGQL(
                cluster_mode=session_info.resource.cluster_mode,
                cluster_size=session_info.resource.cluster_size,
                occupying_slots=ResourceSlotGQL.from_resource_slot(
                    session_info.resource.occupying_slots
                )
                if session_info.resource.occupying_slots
                else ResourceSlotGQL(entries=[]),
                requested_slots=ResourceSlotGQL.from_resource_slot(
                    session_info.resource.requested_slots
                )
                if session_info.resource.requested_slots
                else ResourceSlotGQL(entries=[]),
                scaling_group_name=session_info.resource.scaling_group_name,
                target_sgroup_names=session_info.resource.target_sgroup_names,
                agent_ids=session_info.resource.agent_ids,
            ),
            image=SessionImageInfoGQL(
                images=session_info.image.images,
                tag=session_info.image.tag,
            ),
            mounts=SessionMountInfoGQL(
                vfolder_mounts=[
                    VFolderMountGQL.from_dict(m) for m in session_info.mounts.vfolder_mounts
                ]
                if session_info.mounts.vfolder_mounts
                else None,
            ),
            execution=SessionExecutionInfoGQL(
                environ=session_info.execution.environ,
                bootstrap_script=session_info.execution.bootstrap_script,
                startup_command=session_info.execution.startup_command,
                use_host_network=session_info.execution.use_host_network,
                callback_url=session_info.execution.callback_url,
            ),
            lifecycle=SessionLifecycleInfoGQL(
                status=SessionStatusGQL(session_info.lifecycle.status),
                result=SessionResultGQL(session_info.lifecycle.result),
                created_at=session_info.lifecycle.created_at,
                terminated_at=session_info.lifecycle.terminated_at,
                starts_at=session_info.lifecycle.starts_at,
                status_changed=session_info.lifecycle.status_changed,
                batch_timeout=session_info.lifecycle.batch_timeout,
                status_info=session_info.lifecycle.status_info,
                status_data=SessionStatusDataContainerGQL.from_mapping(
                    session_info.lifecycle.status_data
                ),
                status_history=SessionStatusHistoryGQL.from_mapping(
                    session_info.lifecycle.status_history
                ),
            ),
            metrics=SessionMetricsInfoGQL(
                num_queries=session_info.metrics.num_queries,
                last_stat=SessionStatGQL.from_mapping(session_info.metrics.last_stat),
            ),
            network=SessionNetworkInfoGQL(
                network_type=str(session_info.network.network_type)
                if session_info.network.network_type
                else None,
                network_id=session_info.network.network_id,
            ),
        )


# ========== Connection Types ==========


SessionEdgeGQL = Edge[SessionV2GQL]


@strawberry.type(
    name="SessionConnectionV2",
    description="Added in 26.1.0. Connection type for paginated session results.",
)
class SessionConnectionV2GQL(Connection[SessionV2GQL]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
