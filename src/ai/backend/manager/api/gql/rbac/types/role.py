"""GraphQL types for RBAC role management."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self, cast, override
from uuid import UUID

import strawberry
import strawberry.relay
from strawberry import UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.v2.rbac.request import (
    AdminSearchPermissionsGQLInput,
    SearchRoleAssignmentsInput,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    AssignRoleInput as AssignRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    BulkAssignRoleInput as BulkAssignRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    BulkRevokeRoleInput as BulkRevokeRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    CreateRoleInput as CreateRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    DeleteRoleInput as DeleteRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    MappedScopeNestedFilter as MappedScopeNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    PurgeRoleInput as PurgeRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RevokeRoleInput as RevokeRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RoleAssignmentFilter as RoleAssignmentFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RoleAssignmentOrderBy as RoleAssignmentOrderByDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RoleFilter as RoleFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RoleNestedFilter as RoleNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RoleOrderBy as RoleOrderByDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RoleUsage as RoleUsageDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    RoleUses as RoleUsesDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    UpdateRoleInput as UpdateRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    UserNestedFilter as UserNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    BulkAssignRoleFailureInfo as BulkAssignRoleFailureInfoDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    BulkAssignRoleResultPayload as BulkAssignRoleResultPayloadDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    BulkRevokeRoleFailureInfo as BulkRevokeRoleFailureInfoDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    BulkRevokeRoleResultPayload as BulkRevokeRoleResultPayloadDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    DeleteRolePayload as DeleteRolePayloadDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    PurgeRolePayload as PurgeRolePayloadDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    RoleAssignmentNode,
    RoleNode,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    RoleSourceDTO,
    RoleStatusDTO,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    RoleSourceFilter as RoleSourceFilterDTO,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    RoleStatusFilter as RoleStatusFilterDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter, UUIDFilter, encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_added_field,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin
from ai.backend.manager.api.gql.rbac.types.scope import (
    ScopeInputGQL,
)
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.models.rbac_models.user_role.scopes import (
    RoleRoleAssignmentTarget,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.rbac.types.entity import (
        EntityConnection,
        EntityFilterGQL,
        EntityOrderByGQL,
    )
    from ai.backend.manager.api.gql.rbac.types.entity_node import EntityNodeGQL
    from ai.backend.manager.api.gql.rbac.types.permission import (
        PermissionConnection,
        PermissionFilter,
        PermissionNestedFilterGQL,
        PermissionOrderBy,
        RolePermissionNestedFilterGQL,
    )
    from ai.backend.manager.api.gql.user.types.filters import UserFilterGQL, UserOrderByGQL
    from ai.backend.manager.api.gql.user.types.node import UserV2Connection, UserV2GQL

# ==================== Enums ====================

RoleSourceGQL: type[RoleSourceDTO] = gql_enum(
    BackendAIGQLMeta(added_version="26.3.0", description="Role definition source"),
    RoleSourceDTO,
    name="RoleSource",
)

RoleStatusGQL: type[RoleStatusDTO] = gql_enum(
    BackendAIGQLMeta(added_version="26.3.0", description="Role status"),
    RoleStatusDTO,
    name="RoleStatus",
)


@gql_enum(BackendAIGQLMeta(added_version="26.3.0", description="Role ordering field"))
class RoleOrderField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


# ==================== Node Types ====================


@gql_node_type(BackendAIGQLMeta(added_version="26.3.0", description="RBAC role."), name="Role")
class RoleGQL(PydanticNodeMixin[RoleNode]):
    id: NodeID[str]
    entity_id: UUID = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="UUID of the role.",
        ),
    )
    name: str
    description: str | None
    source: RoleSourceGQL
    status: RoleStatusGQL
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    auto_assign: bool = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description=(
                "When true, the role is automatically granted to a user when the user is added "
                "to a scope this role is registered in."
            ),
        )
    )
    scope_type: str = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Type of the scope the role belongs to.",
        )
    )
    scope_id: UUID = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="ID of the scope the role belongs to.",
        )
    )

    @gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="The scope the role belongs to.",
        )
    )  # type: ignore[misc]
    async def scope(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            EntityNodeGQL,
            strawberry.lazy("ai.backend.manager.api.gql.rbac.types.entity_node"),
        ]
        | None
    ):
        return await info.context.data_loaders.entity_node_loader.load(
            RuntimeEntityID(EntityType.from_name(self.scope_type), self.scope_id)
        )

    @classmethod
    @override
    async def resolve_nodes(  # type: ignore[override]
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        # DataLoader already returns RoleGQL | None via from_pydantic conversion
        results = await info.context.data_loaders.role_loader.load_many([
            RoleID(UUID(nid)) for nid in node_ids
        ])
        return cast(list[Self | None], results)

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.3.0", description="Permissions associated with this role."
        )
    )  # type: ignore[misc]
    async def permissions(
        self,
        info: Info[StrawberryGQLContext],
        filter: Annotated[
            PermissionFilter,
            strawberry.lazy("ai.backend.manager.api.gql.rbac.types.permission"),
        ]
        | None = None,
        order_by: list[
            Annotated[
                PermissionOrderBy,
                strawberry.lazy("ai.backend.manager.api.gql.rbac.types.permission"),
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
            PermissionConnection,
            strawberry.lazy("ai.backend.manager.api.gql.rbac.types.permission"),
        ]
        | None
    ):
        from ai.backend.manager.api.gql.rbac.types.permission import (
            PermissionConnection,
            PermissionEdge,
            PermissionGQL,
        )

        result = await info.context.adapters.rbac.search_role_permissions(
            RoleID(UUID(self.id)),
            AdminSearchPermissionsGQLInput(
                filter=filter.to_pydantic() if filter is not None else None,
                order=[o.to_pydantic() for o in order_by] if order_by is not None else None,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            ),
        )

        edges = [
            PermissionEdge(
                node=PermissionGQL.from_pydantic(item),
                cursor=encode_cursor(str(item.id)),
            )
            for item in result.items
        ]
        return PermissionConnection(
            edges=edges,
            page_info=strawberry.relay.PageInfo(
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=result.total_count,
        )

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.3.0",
            description="Users assigned to this role, as assignment rows.",
            deprecated_version=NEXT_RELEASE_VERSION,
            deprecation_hint="`usersV2`",
        ),
        deprecation_reason=(
            f"Deprecated since {NEXT_RELEASE_VERSION}. Use `usersV2`, which answers with the "
            "users themselves."
        ),
    )  # type: ignore[misc]
    async def users(
        self,
        info: Info[StrawberryGQLContext],
        filter: RoleAssignmentFilter | None = None,
        order_by: list[RoleAssignmentOrderBy] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> RoleAssignmentConnection | None:
        result = await info.context.adapters.rbac.search_role_assignments_in_scope(
            [RoleRoleAssignmentTarget(role_id=RoleID(UUID(self.id)))],
            SearchRoleAssignmentsInput(
                filter=filter.to_pydantic() if filter is not None else None,
                order=[o.to_pydantic() for o in order_by] if order_by is not None else None,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            ),
        )
        edges = [
            RoleAssignmentEdge(
                node=RoleAssignmentGQL.from_pydantic(item),
                cursor=encode_cursor(str(item.id)),
            )
            for item in result.items
        ]
        return RoleAssignmentConnection(
            edges=edges,
            page_info=strawberry.relay.PageInfo(
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=result.total_count,
        )

    @gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Users holding this role.",
        )
    )  # type: ignore[misc]
    async def users_v2(
        self,
        info: Info[StrawberryGQLContext],
        filter: Annotated[
            UserFilterGQL, strawberry.lazy("ai.backend.manager.api.gql.user.types.filters")
        ]
        | None = None,
        order_by: list[
            Annotated[
                UserOrderByGQL,
                strawberry.lazy("ai.backend.manager.api.gql.user.types.filters"),
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
            UserV2Connection,
            strawberry.lazy("ai.backend.manager.api.gql.user.types.node"),
        ]
        | None
    ):
        from strawberry.relay import PageInfo

        from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
        from ai.backend.common.dto.manager.v2.user.request import AdminSearchUsersInput
        from ai.backend.common.dto.manager.v2.user.types import UserScope
        from ai.backend.manager.api.gql.user.types.node import (
            UserV2Connection,
            UserV2Edge,
            UserV2GQL,
        )

        payload = await info.context.adapters.user.gql_scoped_search(
            UserScope(role=[UUIDScope(value=UUID(self.id))]),
            AdminSearchUsersInput(
                filter=filter.to_pydantic() if filter else None,
                order=[o.to_pydantic() for o in order_by] if order_by else None,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            ),
        )
        nodes = [UserV2GQL.from_pydantic(item) for item in payload.items]
        edges = [UserV2Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
        return UserV2Connection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=payload.has_next_page,
                has_previous_page=payload.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=payload.total_count,
        )

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.2",
            description="Scopes this role is registered in.",
            deprecated_version=NEXT_RELEASE_VERSION,
            deprecation_hint="`scope`",
        ),
        deprecation_reason=(
            f"Deprecated since {NEXT_RELEASE_VERSION}. Use `scope`. A role belongs to one "
            "scope, so this connection holds that one scope and ignores `filter` and `order_by`."
        ),
    )  # type: ignore[misc]
    async def scopes(
        self,
        filter: Annotated[
            EntityFilterGQL,
            strawberry.lazy("ai.backend.manager.api.gql.rbac.types.entity"),
        ]
        | None = None,
        order_by: list[
            Annotated[
                EntityOrderByGQL,
                strawberry.lazy("ai.backend.manager.api.gql.rbac.types.entity"),
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
            EntityConnection,
            strawberry.lazy("ai.backend.manager.api.gql.rbac.types.entity"),
        ]
        | None
    ):
        from ai.backend.manager.api.gql.rbac.types.entity import (
            EntityConnection,
            EntityEdge,
            EntityRefGQL,
        )

        page_is_empty = (offset is not None and offset > 0) or any(
            bound == 0 for bound in (first, last, limit)
        )
        edges = (
            []
            if page_is_empty
            else [
                EntityEdge(
                    node=EntityRefGQL.from_role(self),
                    cursor=encode_cursor(self.id),
                )
            ]
        )
        return EntityConnection(
            edges=edges,
            page_info=strawberry.relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=1,
        )


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="RBAC role assignment (user-role association)."
    ),
    name="RoleAssignment",
)
class RoleAssignmentGQL(PydanticNodeMixin[RoleAssignmentNode]):
    id: NodeID[str]
    user_id: UUID = gql_field(description="The assigned user ID.")
    role_id: UUID = gql_field(description="The assigned role ID.")
    granted_by: UUID | None = gql_field(description="The user who granted this assignment.")
    granted_at: datetime

    @classmethod
    @override
    async def resolve_nodes(  # type: ignore[override]
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.role_assignment_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)

    @gql_field(description="The assigned role.")  # type: ignore[misc]
    async def role(self, info: Info[StrawberryGQLContext]) -> RoleGQL | None:
        # DataLoader already returns RoleGQL | None via from_pydantic conversion
        return await info.context.data_loaders.role_loader.load(RoleID(self.role_id))

    @gql_field(description="The assigned user.")  # type: ignore[misc]
    async def user(
        self, info: Info[StrawberryGQLContext]
    ) -> (
        Annotated[
            UserV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.user.types.node"),
        ]
        | None
    ):
        # DataLoader already returns UserV2GQL | None via from_pydantic conversion
        return await info.context.data_loaders.user_loader.load(UserID(self.user_id))

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.3",
            description="The user who granted this role assignment.",
        )
    )  # type: ignore[misc]
    async def granted_by_user(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            UserV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.user.types.node"),
        ]
        | None
    ):
        if self.granted_by is None:
            return None
        return await info.context.data_loaders.user_loader.load(UserID(self.granted_by))


# ==================== Filter Types ====================


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for role source with equality and membership operators.",
        added_version="26.3.0",
    ),
    name="RoleSourceFilter",
)
class RoleSourceFilterGQL(PydanticInputMixin[RoleSourceFilterDTO]):
    equals: RoleSourceGQL | None = gql_field(
        description="Matches roles with this exact source.", default=None
    )
    in_: list[RoleSourceGQL] | None = gql_field(
        description="Matches roles whose source is in this list.", name="in", default=None
    )
    not_equals: RoleSourceGQL | None = gql_field(
        description="Excludes roles with this exact source.", default=None
    )
    not_in: list[RoleSourceGQL] | None = gql_field(
        description="Excludes roles whose source is in this list.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for role status with equality and membership operators.",
        added_version="26.3.0",
    ),
    name="RoleStatusFilter",
)
class RoleStatusFilterGQL(PydanticInputMixin[RoleStatusFilterDTO]):
    equals: RoleStatusGQL | None = gql_field(
        description="Matches roles with this exact status.", default=None
    )
    in_: list[RoleStatusGQL] | None = gql_field(
        description="Matches roles whose status is in this list.", name="in", default=None
    )
    not_equals: RoleStatusGQL | None = gql_field(
        description="Excludes roles with this exact status.", default=None
    )
    not_in: list[RoleStatusGQL] | None = gql_field(
        description="Excludes roles whose status is in this list.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter roles by their user assignments.",
        added_version="26.4.4",
    ),
    name="RoleUserNestedFilter",
)
class RoleUserNestedFilterGQL(PydanticInputMixin[UserNestedFilterDTO]):
    user_id: UUIDFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter roles by the scope they are mapped (registered) to.",
        added_version="26.8.0",
    ),
    name="RoleMappedScopeNestedFilter",
)
class RoleMappedScopeNestedFilterGQL(PydanticInputMixin[MappedScopeNestedFilterDTO]):
    scope_type: StringFilter | None = None
    scope_id: UUIDFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Entities a role uses, whose ids narrow the read.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="RoleUses",
)
class RoleUsesGQL(PydanticInputMixin[RoleUsesDTO]):
    """The entities a role uses, whose ids narrow the read."""

    role_preset: list[UUID] | None = gql_field(
        default=None, description="Role presets the roles were instantiated from."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Uses narrowing a role query; every id is AND-ed. The caller must be able "
            "to read each listed entity, or the request is refused. Only roles the caller "
            "can read are returned, even when a listed entity is tied to others."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="RoleUsage",
)
class RoleUsageGQL(PydanticInputMixin[RoleUsageDTO]):
    """The uses that narrow a role read."""

    uses: RoleUsesGQL | None = gql_field(
        default=None, description="Entities the role uses, whose ids narrow the read."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for roles", added_version="26.3.0"),
    name="RoleFilter",
)
class RoleFilter(PydanticInputMixin[RoleFilterDTO], GQLFilter):
    name: StringFilter | None = None
    source: RoleSourceFilterGQL | None = None
    status: RoleStatusFilterGQL | None = None
    assigned_user: RoleUserNestedFilterGQL | None = gql_field(
        default=None,
        description="Filter roles by the users holding them.",
        deprecation_reason=(
            f"Deprecated since {NEXT_RELEASE_VERSION}. A filter reaching the rows that join"
            " a role to a user cannot check whether the caller may read that user. Search"
            " roles within that user's scope instead."
        ),
    )
    mapped_scope: RoleMappedScopeNestedFilterGQL | None = None
    permissions: (
        Annotated[
            RolePermissionNestedFilterGQL,
            strawberry.lazy("ai.backend.manager.api.gql.rbac.types.permission"),
        ]
        | None
    ) = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Filter by conditions on the role's permission entries.",
        ),
        default=None,
    )

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for roles within a role assignment. Filters assignments that have a role matching all specified conditions.",
        added_version="26.3.0",
    ),
    name="RoleAssignmentRoleNestedFilter",
)
class RoleAssignmentRoleNestedFilterGQL(PydanticInputMixin[RoleNestedFilterDTO]):
    name: StringFilter | None = None
    source: RoleSourceFilterGQL | None = None
    status: RoleStatusFilterGQL | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


_ASSIGNMENT_ROLE_DEPRECATION = (
    f"Deprecated since {NEXT_RELEASE_VERSION}. A filter on the role an assignment names, or"
    " on what that role carries, cannot check whether the caller may read it. Search roles"
    " first and narrow by `roleId`."
)


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for role assignments", added_version="26.3.0"),
    name="RoleAssignmentFilter",
)
class RoleAssignmentFilter(PydanticInputMixin[RoleAssignmentFilterDTO], GQLFilter):
    role_id: UUIDFilter | None = None
    role: RoleAssignmentRoleNestedFilterGQL | None = gql_field(
        default=None,
        description="Filter assignments by the role they name.",
        deprecation_reason=_ASSIGNMENT_ROLE_DEPRECATION,
    )
    permission: (
        Annotated[
            PermissionNestedFilterGQL,
            strawberry.lazy("ai.backend.manager.api.gql.rbac.types.permission"),
        ]
        | None
    ) = gql_field(
        default=None,
        description="Filter assignments by the permissions their role carries.",
        deprecation_reason=_ASSIGNMENT_ROLE_DEPRECATION,
    )
    username: StringFilter | None = None
    email: StringFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


# ==================== OrderBy Types ====================


@gql_pydantic_input(
    BackendAIGQLMeta(description="Order by specification for roles", added_version="26.3.0"),
    name="RoleOrderBy",
)
class RoleOrderBy(PydanticInputMixin[RoleOrderByDTO], GQLOrderBy):
    field: RoleOrderField
    direction: OrderDirection = OrderDirection.DESC


@gql_enum(BackendAIGQLMeta(added_version="26.3.0", description="Role assignment ordering field"))
class RoleAssignmentOrderField(StrEnum):
    USERNAME = "username"
    EMAIL = "email"
    GRANTED_AT = "granted_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Order by specification for role assignments", added_version="26.3.0"
    ),
    name="RoleAssignmentOrderBy",
)
class RoleAssignmentOrderBy(PydanticInputMixin[RoleAssignmentOrderByDTO], GQLOrderBy):
    field: RoleAssignmentOrderField
    direction: OrderDirection = OrderDirection.DESC


# ==================== Input Types ====================


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for creating a role", added_version="26.3.0"),
)
class CreateRoleInput(PydanticInputMixin[CreateRoleInputDTO]):
    name: str
    description: str | None = None
    source: RoleSourceGQL | None = gql_field(
        description="Deprecated and ignored: a created role is always custom.",
        default=None,
        deprecation_reason=(
            f"Deprecated since {NEXT_RELEASE_VERSION}. Ignored: a created role is always custom."
        ),
    )
    auto_assign: bool = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description=(
                "When true, the role is automatically granted to a user when the user is added "
                "to a scope this role is registered in."
            ),
        ),
        default=False,
    )
    scope: ScopeInputGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="The scope the role belongs to.",
        ),
        default=None,
    )
    scopes: list[ScopeInputGQL] | None = gql_field(
        description="Deprecated: use `scope`. Accepts exactly one entry.",
        default=None,
        deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `scope`.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for updating a role", added_version="26.3.0"),
)
class UpdateRoleInput(PydanticInputMixin[UpdateRoleInputDTO]):
    id: UUID
    name: str | None = UNSET
    description: str | None = UNSET
    status: RoleStatusGQL | None = UNSET
    auto_assign: bool | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description=(
                "Updated value for the `auto_assign` flag. When true, the role is automatically "
                "granted to a user when the user is added to a scope this role is registered in."
            ),
        ),
        default=UNSET,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for assigning a role to a user", added_version="26.3.0"),
)
class AssignRoleInput(PydanticInputMixin[AssignRoleInputDTO]):
    user_id: UUID
    role_id: UUID
    project_id: UUID | None = strawberry.UNSET


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for revoking a role from a user", added_version="26.3.0"),
)
class RevokeRoleInput(PydanticInputMixin[RevokeRoleInputDTO]):
    user_id: UUID
    role_id: UUID


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk assigning a role to multiple users", added_version="26.3.0"
    ),
    name="BulkAssignRoleInput",
)
class BulkAssignRoleInputGQL(PydanticInputMixin[BulkAssignRoleInputDTO]):
    role_id: UUID
    user_ids: list[UUID]
    project_id: UUID | None = strawberry.UNSET


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk revoking a role from multiple users", added_version="26.3.0"
    ),
    name="BulkRevokeRoleInput",
)
class BulkRevokeRoleInputGQL(PydanticInputMixin[BulkRevokeRoleInputDTO]):
    role_id: UUID
    user_ids: list[UUID]


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for soft-deleting a role", added_version="26.3.0"),
)
class DeleteRoleInput(PydanticInputMixin[DeleteRoleInputDTO]):
    id: UUID


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for purging a role", added_version="26.3.0"),
)
class PurgeRoleInput(PydanticInputMixin[PurgeRoleInputDTO]):
    id: UUID


# ==================== Payload Types ====================


@gql_pydantic_type(
    BackendAIGQLMeta(added_version="26.3.0", description="Payload for delete role mutation."),
    model=DeleteRolePayloadDTO,
    name="DeleteRolePayload",
)
class DeleteRolePayload(PydanticOutputMixin[DeleteRolePayloadDTO]):
    id: UUID = gql_field(description="ID of the deleted role.")


@gql_pydantic_type(
    BackendAIGQLMeta(added_version="26.3.0", description="Payload for purge role mutation."),
    model=PurgeRolePayloadDTO,
    name="PurgeRolePayload",
)
class PurgeRolePayload(PydanticOutputMixin[PurgeRolePayloadDTO]):
    id: UUID = gql_field(description="ID of the purged role.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Error information for a failed user in bulk role assignment.",
    ),
    model=BulkAssignRoleFailureInfoDTO,
    name="BulkAssignRoleError",
)
class BulkAssignRoleErrorGQL(PydanticOutputMixin[BulkAssignRoleFailureInfoDTO]):
    user_id: UUID = gql_field(description="UUID of the user that failed.")
    message: str = gql_field(description="Error message describing the failure.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Payload for bulk role assignment mutation."
    ),
    model=BulkAssignRoleResultPayloadDTO,
    name="BulkAssignRolePayload",
)
class BulkAssignRolePayloadGQL(PydanticOutputMixin[BulkAssignRoleResultPayloadDTO]):
    assigned: list[RoleAssignmentGQL] = gql_field(
        description="List of successfully created role assignments."
    )
    failed: list[BulkAssignRoleErrorGQL] = gql_field(
        description="List of errors for users that failed to be assigned.",
        deprecation_reason=(
            "Always empty. A user already holding the role keeps it; every other refusal raises."
        ),
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Error information for a failed user in bulk role revocation.",
    ),
    model=BulkRevokeRoleFailureInfoDTO,
    name="BulkRevokeRoleError",
)
class BulkRevokeRoleErrorGQL(PydanticOutputMixin[BulkRevokeRoleFailureInfoDTO]):
    user_id: UUID = gql_field(description="UUID of the user that failed.")
    message: str = gql_field(description="Error message describing the failure.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Payload for bulk role revocation mutation."
    ),
    model=BulkRevokeRoleResultPayloadDTO,
    name="BulkRevokeRolePayload",
)
class BulkRevokeRolePayloadGQL(PydanticOutputMixin[BulkRevokeRoleResultPayloadDTO]):
    revoked: list[RoleAssignmentGQL] = gql_field(
        description="List of successfully revoked role assignments."
    )
    failed: list[BulkRevokeRoleErrorGQL] = gql_field(
        description="List of errors for users that failed to be revoked."
    )


# ==================== Connection Types ====================


RoleEdge = Edge[RoleGQL]


@gql_connection_type(BackendAIGQLMeta(added_version="26.3.0", description="Role connection."))
class RoleConnection(Connection[RoleGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


RoleAssignmentEdge = Edge[RoleAssignmentGQL]


@gql_connection_type(
    BackendAIGQLMeta(added_version="26.3.0", description="Role assignment connection.")
)
class RoleAssignmentConnection(Connection[RoleAssignmentGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
