"""GraphQL types for RBAC role management."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self, cast

import strawberry
import strawberry.relay
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.rbac.request import (
    AdminSearchPermissionsGQLInput,
    AdminSearchRoleAssignmentsGQLInput,
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
    UpdateRoleInput as UpdateRoleInputDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    BulkAssignRoleResultPayload as BulkAssignRoleResultPayloadDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    BulkRevokeRoleResultPayload as BulkRevokeRoleResultPayloadDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    BulkRoleOperationFailureInfo as BulkRoleOperationFailureInfoDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    DeleteRolePayload as DeleteRolePayloadDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    PurgeRolePayload as PurgeRolePayloadDTO,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    RoleAssignmentNode,
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
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter, encode_cursor
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
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.rbac.types.permission import (
        PermissionConnection,
        PermissionFilter,
        PermissionOrderBy,
    )
    from ai.backend.manager.api.gql.user.types.node import UserV2GQL

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
class RoleGQL(PydanticNodeMixin[Any]):
    id: NodeID[str]
    name: str
    description: str | None
    source: RoleSourceGQL
    status: RoleStatusGQL
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @classmethod
    async def resolve_nodes(  # type: ignore[override]
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        # DataLoader already returns RoleGQL | None via from_pydantic conversion
        results = await info.context.data_loaders.role_loader.load_many([
            uuid.UUID(nid) for nid in node_ids
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
    ) -> Annotated[
        PermissionConnection,
        strawberry.lazy("ai.backend.manager.api.gql.rbac.types.permission"),
    ]:
        from ai.backend.manager.api.gql.rbac.types.permission import (
            PermissionConnection,
            PermissionEdge,
            PermissionFilter,
            PermissionGQL,
        )

        # Add role_id filter to scope permissions to this role
        role_filter = PermissionFilter(role_id=uuid.UUID(self.id))
        if filter is not None:
            # Merge with user-provided filter
            combined_filter = PermissionFilter(
                role_id=role_filter.role_id,
                scope_type=filter.scope_type,
                entity_type=filter.entity_type,
            )
        else:
            combined_filter = role_filter

        pydantic_filter = combined_filter.to_pydantic() if combined_filter is not None else None
        pydantic_order = [o.to_pydantic() for o in order_by] if order_by is not None else None

        search_input = AdminSearchPermissionsGQLInput(
            filter=pydantic_filter,
            order=pydantic_order,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
        result = await info.context.adapters.rbac.admin_search_permissions_gql(search_input)

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
        BackendAIGQLMeta(added_version="26.3.0", description="Users assigned to this role.")
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
    ) -> RoleAssignmentConnection:
        # Add role_id filter to scope assignments to this role
        role_filter = RoleAssignmentFilter(role_id=uuid.UUID(self.id))
        if filter is not None:
            # Merge with user-provided filter
            combined_filter = RoleAssignmentFilter(
                role_id=role_filter.role_id,
                role=filter.role,
                username=filter.username,
                email=filter.email,
            )
        else:
            combined_filter = role_filter

        pydantic_filter = combined_filter.to_pydantic() if combined_filter is not None else None
        pydantic_order = [o.to_pydantic() for o in order_by] if order_by is not None else None

        result = await info.context.adapters.rbac.admin_search_role_assignments_gql(
            AdminSearchRoleAssignmentsGQLInput(
                filter=pydantic_filter,
                order=pydantic_order,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            )
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


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="RBAC role assignment (user-role association)."
    ),
    name="RoleAssignment",
)
class RoleAssignmentGQL(PydanticNodeMixin[RoleAssignmentNode]):
    id: NodeID[str]
    user_id: uuid.UUID = gql_field(description="The assigned user ID.")
    role_id: uuid.UUID = gql_field(description="The assigned role ID.")
    granted_by: uuid.UUID | None = gql_field(description="The user who granted this assignment.")
    granted_at: datetime

    @classmethod
    async def resolve_nodes(  # type: ignore[override]
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        # DataLoader already returns RoleAssignmentGQL | None via from_pydantic conversion
        results = await info.context.data_loaders.role_assignment_loader.load_many([
            uuid.UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)

    @gql_field(description="The assigned role.")  # type: ignore[misc]
    async def role(self, info: Info[StrawberryGQLContext]) -> RoleGQL | None:
        # DataLoader already returns RoleGQL | None via from_pydantic conversion
        return await info.context.data_loaders.role_loader.load(self.role_id)

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
        return await info.context.data_loaders.user_loader.load(self.user_id)


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
    BackendAIGQLMeta(description="Filter for roles", added_version="26.3.0"),
    name="RoleFilter",
)
class RoleFilter(PydanticInputMixin[RoleFilterDTO], GQLFilter):
    name: StringFilter | None = None
    source: RoleSourceFilterGQL | None = None
    status: RoleStatusFilterGQL | None = None

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


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for role assignments", added_version="26.3.0"),
    name="RoleAssignmentFilter",
)
class RoleAssignmentFilter(PydanticInputMixin[RoleAssignmentFilterDTO], GQLFilter):
    role_id: uuid.UUID | None = None
    role: RoleAssignmentRoleNestedFilterGQL | None = None
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
    source: RoleSourceGQL | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for updating a role", added_version="26.3.0"),
)
class UpdateRoleInput(PydanticInputMixin[UpdateRoleInputDTO]):
    id: uuid.UUID
    name: str | None = UNSET
    description: str | None = UNSET
    status: RoleStatusGQL | None = UNSET


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for assigning a role to a user", added_version="26.3.0"),
)
class AssignRoleInput(PydanticInputMixin[AssignRoleInputDTO]):
    user_id: uuid.UUID
    role_id: uuid.UUID


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for revoking a role from a user", added_version="26.3.0"),
)
class RevokeRoleInput(PydanticInputMixin[RevokeRoleInputDTO]):
    user_id: uuid.UUID
    role_id: uuid.UUID


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk assigning a role to multiple users", added_version="26.3.0"
    ),
    name="BulkAssignRoleInput",
)
class BulkAssignRoleInputGQL(PydanticInputMixin[BulkAssignRoleInputDTO]):
    role_id: uuid.UUID
    user_ids: list[uuid.UUID]


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk revoking a role from multiple users", added_version="26.3.0"
    ),
    name="BulkRevokeRoleInput",
)
class BulkRevokeRoleInputGQL(PydanticInputMixin[BulkRevokeRoleInputDTO]):
    role_id: uuid.UUID
    user_ids: list[uuid.UUID]


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for soft-deleting a role", added_version="26.3.0"),
)
class DeleteRoleInput(PydanticInputMixin[DeleteRoleInputDTO]):
    id: uuid.UUID


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for purging a role", added_version="26.3.0"),
)
class PurgeRoleInput(PydanticInputMixin[PurgeRoleInputDTO]):
    id: uuid.UUID


# ==================== Payload Types ====================


@gql_pydantic_type(
    BackendAIGQLMeta(added_version="26.3.0", description="Payload for delete role mutation."),
    model=DeleteRolePayloadDTO,
    fields=["id"],
    name="DeleteRolePayload",
)
class DeleteRolePayload(PydanticOutputMixin[DeleteRolePayloadDTO]):
    id: ID = gql_field(description="ID of the deleted role.")


@gql_pydantic_type(
    BackendAIGQLMeta(added_version="26.3.0", description="Payload for purge role mutation."),
    model=PurgeRolePayloadDTO,
    fields=["id"],
    name="PurgeRolePayload",
)
class PurgeRolePayload(PydanticOutputMixin[PurgeRolePayloadDTO]):
    id: ID = gql_field(description="ID of the purged role.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Error information for a failed user in bulk role assignment.",
    ),
    model=BulkRoleOperationFailureInfoDTO,
    name="BulkAssignRoleError",
)
class BulkAssignRoleErrorGQL(PydanticOutputMixin[BulkRoleOperationFailureInfoDTO]):
    user_id: uuid.UUID = gql_field(description="UUID of the user that failed.")
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
        description="List of errors for users that failed to be assigned."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Error information for a failed user in bulk role revocation.",
    ),
    model=BulkRoleOperationFailureInfoDTO,
    name="BulkRevokeRoleError",
)
class BulkRevokeRoleErrorGQL(PydanticOutputMixin[BulkRoleOperationFailureInfoDTO]):
    user_id: uuid.UUID = gql_field(description="UUID of the user that failed.")
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
