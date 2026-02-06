"""GraphQL types for session management."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Self
from uuid import UUID

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.base import OrderDirection
from ai.backend.manager.api.gql.common.types import (
    SessionResultGQL,
    SessionTypesGQL,
)
from ai.backend.manager.api.gql.fair_share.types.common import ResourceSlotGQL
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.data.session.types import SessionInfo, SessionStatus
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder

SessionStatusGQL = strawberry.enum(
    SessionStatus, name="SessionStatus", description="Added in 26.2.0"
)


# ========== Order and Filter Types ==========


@strawberry.enum(
    name="SessionOrderField",
    description="Added in 26.2.0. Fields available for ordering sessions.",
)
class SessionOrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    ID = "id"
    NAME = "name"


@strawberry.input(
    name="SessionStatusFilter", description="Added in 26.2.0. Filter for session status."
)
class SessionStatusFilterGQL:
    in_: list[SessionStatusGQL] | None = strawberry.field(name="in", default=None)
    not_in: list[SessionStatusGQL] | None = None

    def build_condition(self) -> QueryCondition | None:
        raise NotImplementedError


@strawberry.input(
    name="SessionFilter", description="Added in 26.2.0. Filter criteria for querying sessions."
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
    name="SessionOrderBy", description="Added in 26.2.0. Ordering specification for sessions."
)
class SessionOrderByGQL(GQLOrderBy):
    field: SessionOrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC

    def to_query_order(self) -> QueryOrder:
        raise NotImplementedError


# ========== Session Info Sub-Types ==========


@strawberry.type(
    name="SessionIdentityInfo",
    description="Added in 26.2.0. Basic identity information for a session.",
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
    description="Added in 26.2.0. Metadata information for a session.",
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
    description="Added in 26.2.0. Resource allocation information for a session.",
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
    name="SessionLifecycleInfo",
    description="Added in 26.2.0. Lifecycle status and timestamps for a session.",
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


@strawberry.type(
    name="SessionNetworkInfo",
    description="Added in 26.2.0. Network configuration for a session.",
)
class SessionNetworkInfoGQL:
    network_type: str | None = strawberry.field(description="Type of network used by the session.")
    network_id: str | None = strawberry.field(description="ID of the network if applicable.")


# ========== Main Session Type ==========


@strawberry.type(
    name="SessionV2",
    description="Added in 26.2.0. Represents a compute session in Backend.AI.",
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
    lifecycle: SessionLifecycleInfoGQL = strawberry.field(
        description="Lifecycle status and timestamps."
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
    description="Added in 26.2.0. Connection type for paginated session results.",
)
class SessionConnectionV2GQL(Connection[SessionV2GQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
