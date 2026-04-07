"""Resource Policy V2 GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.resource_policy.response import (
    KeypairResourcePolicyNode,
    ProjectResourcePolicyNode,
    UserResourcePolicyNode,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.common_types import (
    BinarySizeInfoGQL,
    ResourceLimitEntryGQL,
    VFolderHostPermissionEntryGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_connection_type,
    gql_field,
    gql_node_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin

# ── Keypair Resource Policy ──


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Keypair resource policy defining session and storage limits for API keypairs.",
    ),
    name="KeypairResourcePolicyV2",
)
class KeypairResourcePolicyV2GQL(PydanticNodeMixin[KeypairResourcePolicyNode]):
    id: NodeID[str] = gql_field(description="Policy name (primary key).")
    name: str = gql_field(description="Policy name.")
    created_at: datetime | None = gql_field(description="Timestamp when the policy was created.")
    default_for_unspecified: str = gql_field(
        description="Default resource allocation for unspecified slots (LIMITED or UNLIMITED)."
    )
    total_resource_slots: list[ResourceLimitEntryGQL] = gql_field(
        description="Total resource slot limits for sessions."
    )
    max_session_lifetime: int = gql_field(description="Maximum session lifetime in seconds.")
    max_concurrent_sessions: int = gql_field(description="Maximum concurrent sessions allowed.")
    max_pending_session_count: int | None = gql_field(
        description="Maximum pending sessions. Null means unlimited."
    )
    max_pending_session_resource_slots: list[ResourceLimitEntryGQL] | None = gql_field(
        description="Maximum resource slots for pending sessions. Null means unlimited."
    )
    max_concurrent_sftp_sessions: int = gql_field(
        description="Maximum concurrent SFTP sessions allowed."
    )
    max_containers_per_session: int = gql_field(
        description="Maximum containers allowed per session."
    )
    idle_timeout: int = gql_field(description="Idle timeout for sessions in seconds.")
    allowed_vfolder_hosts: list[VFolderHostPermissionEntryGQL] = gql_field(
        description="Allowed vfolder host permissions."
    )


KeypairResourcePolicyV2Edge = Edge[KeypairResourcePolicyV2GQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated connection for keypair resource policies.",
    )
)
class KeypairResourcePolicyV2Connection(Connection[KeypairResourcePolicyV2GQL]):
    count: int = gql_field(description="Total number of matching policies.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# ── User Resource Policy ──


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="User resource policy defining vfolder and quota limits per user.",
    ),
    name="UserResourcePolicyV2",
)
class UserResourcePolicyV2GQL(PydanticNodeMixin[UserResourcePolicyNode]):
    id: NodeID[str] = gql_field(description="Policy name (primary key).")
    name: str = gql_field(description="Policy name.")
    created_at: datetime | None = gql_field(description="Timestamp when the policy was created.")
    max_vfolder_count: int = gql_field(description="Maximum vfolders a user can create.")
    max_concurrent_logins: int | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description=(
                "Maximum number of concurrent authenticated login sessions per user."
                " Null means unlimited."
                " Distinct from keypair_resource_policies.max_concurrent_sessions"
                " which caps compute sessions."
            ),
        ),
    )
    max_quota_scope_size: BinarySizeInfoGQL = gql_field(description="Maximum quota scope size.")
    max_session_count_per_model_session: int = gql_field(
        description="Maximum sessions per model session."
    )
    max_customized_image_count: int = gql_field(
        description="Maximum customized images a user can create."
    )


UserResourcePolicyV2Edge = Edge[UserResourcePolicyV2GQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated connection for user resource policies.",
    )
)
class UserResourcePolicyV2Connection(Connection[UserResourcePolicyV2GQL]):
    count: int = gql_field(description="Total number of matching policies.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# ── Project Resource Policy ──


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Project resource policy defining vfolder, quota, and network limits per project.",
    ),
    name="ProjectResourcePolicyV2",
)
class ProjectResourcePolicyV2GQL(PydanticNodeMixin[ProjectResourcePolicyNode]):
    id: NodeID[str] = gql_field(description="Policy name (primary key).")
    name: str = gql_field(description="Policy name.")
    created_at: datetime | None = gql_field(description="Timestamp when the policy was created.")
    max_vfolder_count: int = gql_field(description="Maximum vfolders a project can have.")
    max_quota_scope_size: BinarySizeInfoGQL = gql_field(description="Maximum quota scope size.")
    max_network_count: int = gql_field(
        description="Maximum networks a project can create. -1 means unlimited."
    )


ProjectResourcePolicyV2Edge = Edge[ProjectResourcePolicyV2GQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated connection for project resource policies.",
    )
)
class ProjectResourcePolicyV2Connection(Connection[ProjectResourcePolicyV2GQL]):
    count: int = gql_field(description="Total number of matching policies.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
