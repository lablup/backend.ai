"""Resource Policy V2 GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any

import strawberry
from strawberry import Info
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
from ai.backend.manager.api.gql.types import StrawberryGQLContext

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.keypair.types.filters import (
        KeypairFilterGQL,
        KeypairOrderByGQL,
    )
    from ai.backend.manager.api.gql.keypair.types.node import KeyPairConnection

# ── Keypair Resource Policy ──


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
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

    @gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Keypairs assigned to this resource policy.",
        )
    )  # type: ignore[misc]
    async def keypairs(
        self,
        info: Info[StrawberryGQLContext],
        filter: Annotated[
            KeypairFilterGQL,
            strawberry.lazy("ai.backend.manager.api.gql.keypair.types.filters"),
        ]
        | None = None,
        order_by: list[
            Annotated[
                KeypairOrderByGQL,
                strawberry.lazy("ai.backend.manager.api.gql.keypair.types.filters"),
            ]
        ]
        | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> (
        Annotated[
            KeyPairConnection,
            strawberry.lazy("ai.backend.manager.api.gql.keypair.types.node"),
        ]
        | None
    ):
        from strawberry.relay import PageInfo

        from ai.backend.common.data.filter_specs import StringMatchSpec
        from ai.backend.common.dto.manager.v2.keypair.request import SearchMyKeypairsRequest
        from ai.backend.manager.api.gql.base import encode_cursor
        from ai.backend.manager.api.gql.keypair.types.node import (
            KeyPairConnection,
            KeyPairEdge,
            KeyPairGQL,
        )
        from ai.backend.manager.models.keypair.conditions import KeypairConditions

        # Scope the search to the current user's keypairs assigned to this resource policy.
        # search_my_keypairs resolves current_user() internally; the resource-policy scope
        # is applied as a base condition before any user-supplied filters so it cannot be escaped.
        result = await info.context.adapters.user.search_my_keypairs(
            SearchMyKeypairsRequest(
                filter=filter.to_pydantic() if filter is not None else None,
                order=[o.to_pydantic() for o in order_by] if order_by is not None else None,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            ),
            base_conditions=[
                KeypairConditions.by_resource_policy_equals(
                    StringMatchSpec(self.name, case_insensitive=False, negated=False)
                )
            ],
        )
        nodes = [KeyPairGQL.from_pydantic(item) for item in result.items]
        edges = [KeyPairEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
        return KeyPairConnection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=result.total_count,
        )


KeypairResourcePolicyV2Edge = Edge[KeypairResourcePolicyV2GQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
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
        added_version="26.4.2",
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
            added_version="26.4.2",
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
        added_version="26.4.2",
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
        added_version="26.4.2",
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
        added_version="26.4.2",
        description="Paginated connection for project resource policies.",
    )
)
class ProjectResourcePolicyV2Connection(Connection[ProjectResourcePolicyV2GQL]):
    count: int = gql_field(description="Total number of matching policies.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
