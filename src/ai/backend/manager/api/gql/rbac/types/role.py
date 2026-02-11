"""GraphQL types for RBAC role management."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Self, override

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.data.permission.types import (
    RoleSource,
    RoleStatus,
)
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.data.permission.role import (
    AssignedUserData,
    RoleData,
    RoleDetailData,
    UserRoleAssignmentData,
    UserRoleAssignmentInput,
    UserRoleRevocationData,
    UserRoleRevocationInput,
)
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.permission_controller.creators import RoleCreatorSpec
from ai.backend.manager.repositories.permission_controller.options import (
    AssignedUserConditions,
    RoleConditions,
    RoleOrders,
)
from ai.backend.manager.repositories.permission_controller.updaters import RoleUpdaterSpec
from ai.backend.manager.types import OptionalState, TriState

# ==================== Enums ====================


@strawberry.enum(name="RoleSource", description="Role definition source")
class RoleSourceGQL(StrEnum):
    SYSTEM = "system"
    CUSTOM = "custom"

    @classmethod
    def from_internal(cls, value: RoleSource) -> RoleSourceGQL:
        return cls(value.value)

    def to_internal(self) -> RoleSource:
        return RoleSource(self.value)


@strawberry.enum(name="RoleStatus", description="Role status")
class RoleStatusGQL(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"

    @classmethod
    def from_internal(cls, value: RoleStatus) -> RoleStatusGQL:
        return cls(value.value)

    def to_internal(self) -> RoleStatus:
        return RoleStatus(self.value)


@strawberry.enum
class RoleOrderField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


# ==================== Node Types ====================


@strawberry.type(description="RBAC role")
class RoleGQL(Node):
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
        # TODO: Implement using get_role or get_role_detail processor
        return []

    @classmethod
    def from_dataclass(cls, data: RoleData | RoleDetailData) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            description=data.description,
            source=RoleSourceGQL.from_internal(data.source),
            status=RoleStatusGQL.from_internal(data.status),
            created_at=data.created_at,
            updated_at=data.updated_at,
            deleted_at=data.deleted_at,
        )


@strawberry.type(description="RBAC role assignment (user-role association)")
class RoleAssignmentGQL(Node):
    id: NodeID[str]
    _user_id: strawberry.Private[uuid.UUID]
    _role_id: strawberry.Private[uuid.UUID]
    _granted_by: strawberry.Private[uuid.UUID | None]
    granted_at: datetime

    @strawberry.field(description="The assigned user ID.")  # type: ignore[misc]
    def user_id(self) -> ID:
        return ID(str(self._user_id))

    @strawberry.field(description="The assigned role ID.")  # type: ignore[misc]
    def role_id(self) -> ID:
        return ID(str(self._role_id))

    @strawberry.field(description="The user who granted this assignment.")  # type: ignore[misc]
    def granted_by(self) -> ID | None:
        return ID(str(self._granted_by)) if self._granted_by else None

    @classmethod
    async def resolve_nodes(  # type: ignore[override]
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        # TODO: Implement after adding batch get user-role assignment method to repository
        return []

    @classmethod
    def from_dataclass(cls, data: AssignedUserData) -> Self:
        return cls(
            id=ID(f"{data.user_id}"),
            _user_id=data.user_id,
            _role_id=uuid.UUID(int=0),  # Populated from context
            _granted_by=data.granted_by,
            granted_at=data.granted_at,
        )

    @classmethod
    def from_assignment_data(cls, data: UserRoleAssignmentData) -> Self:
        return cls(
            id=ID(f"{data.user_id}:{data.role_id}"),
            _user_id=data.user_id,
            _role_id=data.role_id,
            _granted_by=data.granted_by,
            granted_at=datetime.now(tz=UTC),
        )

    @classmethod
    def from_revocation_data(cls, data: UserRoleRevocationData) -> Self:
        return cls(
            id=ID(f"{data.user_id}:{data.role_id}"),
            _user_id=data.user_id,
            _role_id=data.role_id,
            _granted_by=None,
            granted_at=datetime.now(tz=UTC),
        )


# ==================== Filter Types ====================


@strawberry.input(description="Filter for roles")
class RoleFilter(GQLFilter):
    name: StringFilter | None = None
    source: list[RoleSourceGQL] | None = None
    status: list[RoleStatusGQL] | None = None

    AND: list[RoleFilter] | None = None
    OR: list[RoleFilter] | None = None
    NOT: RoleFilter | None = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if self.name is not None:
            condition = self.name.build_query_condition(
                contains_factory=RoleConditions.by_name_contains,
                equals_factory=RoleConditions.by_name_equals,
                starts_with_factory=RoleConditions.by_name_starts_with,
                ends_with_factory=RoleConditions.by_name_ends_with,
            )
            if condition:
                conditions.append(condition)

        if self.source is not None and len(self.source) > 0:
            conditions.append(RoleConditions.by_sources([s.to_internal() for s in self.source]))

        if self.status is not None and len(self.status) > 0:
            conditions.append(RoleConditions.by_statuses([s.to_internal() for s in self.status]))

        return conditions


@strawberry.input(description="Filter for role assignments")
class RoleAssignmentFilter(GQLFilter):
    role_id: uuid.UUID | None = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if self.role_id is not None:
            conditions.append(AssignedUserConditions.by_role_id(self.role_id))

        return conditions


# ==================== OrderBy Types ====================


@strawberry.input(description="Order by specification for roles")
class RoleOrderBy(GQLOrderBy):
    field: RoleOrderField
    direction: OrderDirection = OrderDirection.DESC

    @override
    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case RoleOrderField.NAME:
                return RoleOrders.name(ascending)
            case RoleOrderField.CREATED_AT:
                return RoleOrders.created_at(ascending)
            case RoleOrderField.UPDATED_AT:
                return RoleOrders.updated_at(ascending)


# ==================== Input Types ====================


@strawberry.input(description="Input for creating a role")
class CreateRoleInput:
    name: str
    description: str | None = None
    source: RoleSourceGQL | None = None

    def to_creator(self) -> Creator[RoleRow]:
        return Creator(
            spec=RoleCreatorSpec(
                name=self.name,
                source=self.source.to_internal() if self.source is not None else RoleSource.CUSTOM,
                status=RoleStatus.ACTIVE,
                description=self.description,
            )
        )


@strawberry.input(description="Input for updating a role")
class UpdateRoleInput:
    id: uuid.UUID
    name: str | None = None
    description: str | None = None

    def to_updater(self) -> Updater[RoleRow]:
        spec = RoleUpdaterSpec(
            name=OptionalState.update(self.name) if self.name is not None else OptionalState.nop(),
            description=(
                TriState.update(self.description)
                if self.description is not None
                else TriState.nop()
            ),
        )
        return Updater(spec=spec, pk_value=self.id)


@strawberry.input(description="Input for assigning a role to a user")
class AssignRoleInput:
    user_id: uuid.UUID
    role_id: uuid.UUID

    def to_input(self) -> UserRoleAssignmentInput:
        return UserRoleAssignmentInput(
            user_id=self.user_id,
            role_id=self.role_id,
        )


@strawberry.input(description="Input for revoking a role from a user")
class RevokeRoleInput:
    user_id: uuid.UUID
    role_id: uuid.UUID

    def to_input(self) -> UserRoleRevocationInput:
        return UserRoleRevocationInput(
            user_id=self.user_id,
            role_id=self.role_id,
        )


# ==================== Connection Types ====================


RoleEdge = Edge[RoleGQL]


@strawberry.type(description="Role connection")
class RoleConnection(Connection[RoleGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


RoleAssignmentEdge = Edge[RoleAssignmentGQL]


@strawberry.type(description="Role assignment connection")
class RoleAssignmentConnection(Connection[RoleAssignmentGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
