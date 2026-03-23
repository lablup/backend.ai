"""Query conditions for RBAC models."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.data.permission.id import ObjectId
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    RoleSource,
    ScopeType,
)
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import (
    ObjectPermissionRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base import QueryCondition


class RoleConditions:
    """Query conditions for roles."""

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = RoleRow.name.ilike(f"%{spec.value}%")
            else:
                condition = RoleRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(RoleRow.name) == spec.value.lower()
            else:
                condition = RoleRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = RoleRow.name.ilike(f"{spec.value}%")
            else:
                condition = RoleRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = RoleRow.name.ilike(f"%{spec.value}")
            else:
                condition = RoleRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_sources(sources: list[RoleSource]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.source.in_(sources)

        return inner

    @staticmethod
    def by_source_equals(source: RoleSource) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.source == source

        return inner

    @staticmethod
    def by_source_not_equals(source: RoleSource) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.source != source

        return inner

    @staticmethod
    def by_source_not_in(sources: Collection[RoleSource]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.source.not_in(sources)

        return inner

    @staticmethod
    def by_statuses(statuses: list[RoleStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.status.in_(statuses)

        return inner

    @staticmethod
    def by_status_equals(status: RoleStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.status == status

        return inner

    @staticmethod
    def by_status_not_equals(status: RoleStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.status != status

        return inner

    @staticmethod
    def by_status_not_in(statuses: Collection[RoleStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.status.not_in(statuses)

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(RoleRow.created_at).where(RoleRow.id == cursor_uuid).scalar_subquery()
            )
            return RoleRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(RoleRow.created_at).where(RoleRow.id == cursor_uuid).scalar_subquery()
            )
            return RoleRow.created_at > subquery

        return inner

    @staticmethod
    def by_has_permission_for(entity_type: EntityType) -> QueryCondition:
        """Filter roles having permission for entity type.

        Requires JOIN with ObjectPermissionRow.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ObjectPermissionRow.entity_type == entity_type

        return inner

    @staticmethod
    def by_ids(role_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.id.in_(role_ids)

        return inner


class PermissionConditions:
    """Query conditions for permissions."""

    @staticmethod
    def by_scope_id(scope_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.scope_id == scope_id

        return inner

    @staticmethod
    def by_scope_types(scope_types: list[ScopeType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.scope_type.in_(scope_types)

        return inner

    @staticmethod
    def by_entity_types(entity_types: list[EntityType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.entity_type.in_(entity_types)

        return inner

    @staticmethod
    def by_operations(operations: list[OperationType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.operation.in_(operations)

        return inner


class AssignedUserConditions:
    """Query conditions for assigned users."""

    @staticmethod
    def by_user_id(user_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRoleRow.user_id == user_id

        return inner

    @staticmethod
    def by_role_id(role_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRoleRow.role_id == role_id

        return inner

    @staticmethod
    def by_role_ids(role_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRoleRow.role_id.in_(role_ids)

        return inner

    @staticmethod
    def by_username_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.username.ilike(f"%{spec.value}%")
            else:
                condition = UserRow.username.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_username_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(UserRow.username) == spec.value.lower()
            else:
                condition = UserRow.username == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_username_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.username.ilike(f"{spec.value}%")
            else:
                condition = UserRow.username.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_username_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.username.ilike(f"%{spec.value}")
            else:
                condition = UserRow.username.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_email_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.email.ilike(f"%{spec.value}%")
            else:
                condition = UserRow.email.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_email_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(UserRow.email) == spec.value.lower()
            else:
                condition = UserRow.email == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_email_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.email.ilike(f"{spec.value}%")
            else:
                condition = UserRow.email.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_email_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.email.ilike(f"%{spec.value}")
            else:
                condition = UserRow.email.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_granted_by_equals(granted_by: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRoleRow.granted_by == granted_by

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor)."""
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRoleRow.id > cursor_uuid

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor)."""
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRoleRow.id < cursor_uuid

        return inner

    @staticmethod
    def by_ids(assignment_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRoleRow.id.in_(assignment_ids)

        return inner

    @staticmethod
    def by_user_ids(user_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRoleRow.user_id.in_(user_ids)

        return inner

    @staticmethod
    def by_role_and_user_ids(
        pairs: Collection[tuple[uuid.UUID, uuid.UUID]],
    ) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.tuple_(UserRoleRow.role_id, UserRoleRow.user_id).in_(pairs)

        return inner

    @staticmethod
    def exists_role_combined(role_conditions: list[QueryCondition]) -> QueryCondition:
        """Combine multiple role conditions into single EXISTS subquery."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = sa.select(sa.literal(1)).where(RoleRow.id == UserRoleRow.role_id)
            for cond in role_conditions:
                subq = subq.where(cond())
            return sa.exists(subq)

        return inner

    @staticmethod
    def exists_user_combined(user_conditions: list[QueryCondition]) -> QueryCondition:
        """Combine multiple user conditions into single EXISTS subquery."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = (
                sa.select(sa.literal(1))
                .where(UserRow.uuid == UserRoleRow.user_id)
                .correlate(UserRoleRow)
            )
            for cond in user_conditions:
                subq = subq.where(cond())
            return sa.exists(subq)

        return inner

    @staticmethod
    def exists_permission_combined(permission_conditions: list[QueryCondition]) -> QueryCondition:
        """Combine multiple permission conditions into single EXISTS subquery."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = (
                sa.select(sa.literal(1))
                .where(PermissionRow.role_id == UserRoleRow.role_id)
                .correlate(UserRoleRow)
            )
            for cond in permission_conditions:
                subq = subq.where(cond())
            return sa.exists(subq)

        return inner


class DomainScopeConditions:
    """Query conditions for domain scope IDs."""

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainRow.name.ilike(f"%{spec.value}%")
            else:
                condition = DomainRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(DomainRow.name) == spec.value.lower()
            else:
                condition = DomainRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainRow.name.ilike(f"{spec.value}%")
            else:
                condition = DomainRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainRow.name.ilike(f"%{spec.value}")
            else:
                condition = DomainRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner


class ProjectScopeConditions:
    """Query conditions for project (group) scope IDs."""

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = GroupRow.name.ilike(f"%{spec.value}%")
            else:
                condition = GroupRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(GroupRow.name) == spec.value.lower()
            else:
                condition = GroupRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = GroupRow.name.ilike(f"{spec.value}%")
            else:
                condition = GroupRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = GroupRow.name.ilike(f"%{spec.value}")
            else:
                condition = GroupRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner


class UserScopeConditions:
    """Query conditions for user scope IDs."""

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        """Search in both username and email."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                username_cond = UserRow.username.ilike(f"%{spec.value}%")
                email_cond = UserRow.email.ilike(f"%{spec.value}%")
            else:
                username_cond = UserRow.username.like(f"%{spec.value}%")
                email_cond = UserRow.email.like(f"%{spec.value}%")
            condition = sa.or_(username_cond, email_cond)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        """Match username or email exactly."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                username_cond = sa.func.lower(UserRow.username) == spec.value.lower()
                email_cond = sa.func.lower(UserRow.email) == spec.value.lower()
            else:
                username_cond = UserRow.username == spec.value
                email_cond = UserRow.email == spec.value
            condition = sa.or_(username_cond, email_cond)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        """Search in both username and email."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                username_cond = UserRow.username.ilike(f"{spec.value}%")
                email_cond = UserRow.email.ilike(f"{spec.value}%")
            else:
                username_cond = UserRow.username.like(f"{spec.value}%")
                email_cond = UserRow.email.like(f"{spec.value}%")
            condition = sa.or_(username_cond, email_cond)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        """Search in both username and email."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                username_cond = UserRow.username.ilike(f"%{spec.value}")
                email_cond = UserRow.email.ilike(f"%{spec.value}")
            else:
                username_cond = UserRow.username.like(f"%{spec.value}")
                email_cond = UserRow.email.like(f"%{spec.value}")
            condition = sa.or_(username_cond, email_cond)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner


class EntityScopeConditions:
    """Query conditions for entity scope search."""

    @staticmethod
    def by_scope_type(scope_type: ScopeType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AssociationScopesEntitiesRow.scope_type == scope_type

        return inner

    @staticmethod
    def by_scope_id(scope_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AssociationScopesEntitiesRow.scope_id == scope_id

        return inner

    @staticmethod
    def by_entity_type(entity_type: EntityType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AssociationScopesEntitiesRow.entity_type == entity_type

        return inner

    @staticmethod
    def by_object_ids(
        object_ids: Collection[ObjectId],
    ) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.tuple_(
                AssociationScopesEntitiesRow.entity_type,
                AssociationScopesEntitiesRow.entity_id,
            ).in_([(oid.entity_type, oid.entity_id) for oid in object_ids])

        return inner

    @staticmethod
    def by_entity_id_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AssociationScopesEntitiesRow.entity_id.ilike(f"%{spec.value}%")
            else:
                condition = AssociationScopesEntitiesRow.entity_id.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_entity_id_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = (
                    sa.func.lower(AssociationScopesEntitiesRow.entity_id) == spec.value.lower()
                )
            else:
                condition = AssociationScopesEntitiesRow.entity_id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_entity_id_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AssociationScopesEntitiesRow.entity_id.ilike(f"{spec.value}%")
            else:
                condition = AssociationScopesEntitiesRow.entity_id.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_entity_id_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AssociationScopesEntitiesRow.entity_id.ilike(f"%{spec.value}")
            else:
                condition = AssociationScopesEntitiesRow.entity_id.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_ids(ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AssociationScopesEntitiesRow.id.in_(ids)

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get (registered_at, id) of the cursor row and compare.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            cursor_subq = (
                sa.select(
                    AssociationScopesEntitiesRow.registered_at,
                    AssociationScopesEntitiesRow.id,
                )
                .where(AssociationScopesEntitiesRow.id == uuid.UUID(cursor_id))
                .scalar_subquery()
            )
            return (
                sa.tuple_(
                    AssociationScopesEntitiesRow.registered_at,
                    AssociationScopesEntitiesRow.id,
                )
                < cursor_subq
            )

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get (registered_at, id) of the cursor row and compare.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            cursor_subq = (
                sa.select(
                    AssociationScopesEntitiesRow.registered_at,
                    AssociationScopesEntitiesRow.id,
                )
                .where(AssociationScopesEntitiesRow.id == uuid.UUID(cursor_id))
                .scalar_subquery()
            )
            return (
                sa.tuple_(
                    AssociationScopesEntitiesRow.registered_at,
                    AssociationScopesEntitiesRow.id,
                )
                > cursor_subq
            )

        return inner


class ScopedPermissionConditions:
    """Query conditions for scoped permissions."""

    @staticmethod
    def by_entity_type(entity_type: EntityType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.entity_type == entity_type

        return inner

    @staticmethod
    def by_operation(operation: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.operation == operation

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor)."""
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.id > cursor_uuid

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor)."""
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.id < cursor_uuid

        return inner

    @staticmethod
    def by_role_id(role_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.role_id == role_id

        return inner

    @staticmethod
    def by_scope_type(scope_type: ScopeType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.scope_type == scope_type

        return inner

    @staticmethod
    def by_ids(permission_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.id.in_(permission_ids)

        return inner

    @staticmethod
    def by_role_ids(role_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.role_id.in_(role_ids)

        return inner


class ObjectPermissionConditions:
    """Query conditions for object permissions."""

    @staticmethod
    def by_role_id(role_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ObjectPermissionRow.role_id == role_id

        return inner

    @staticmethod
    def by_entity_type(entity_type: EntityType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ObjectPermissionRow.entity_type == entity_type

        return inner

    @staticmethod
    def by_entity_id(entity_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ObjectPermissionRow.entity_id == entity_id

        return inner

    @staticmethod
    def by_operation(operation: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ObjectPermissionRow.operation == operation

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor)."""
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ObjectPermissionRow.id > cursor_uuid

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor)."""
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ObjectPermissionRow.id < cursor_uuid

        return inner
