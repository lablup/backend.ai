from __future__ import annotations

import uuid

import sqlalchemy as sa

from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import EntityType, RoleSource, ScopeType
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import (
    ObjectPermissionRow,
)
from ai.backend.manager.models.rbac_models.permission.permission_group import (
    PermissionGroupRow,
)
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder


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
    def by_statuses(statuses: list[RoleStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.status.in_(statuses)

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
    def by_scope_type(scope_type: ScopeType) -> QueryCondition:
        """Filter roles by scope type.

        Requires JOIN with PermissionGroupRow.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionGroupRow.scope_type == scope_type

        return inner

    @staticmethod
    def by_scope_id(scope_id: str) -> QueryCondition:
        """Filter roles by scope ID.

        Requires JOIN with PermissionGroupRow.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionGroupRow.scope_id == scope_id

        return inner

    @staticmethod
    def by_has_permission_for(entity_type: EntityType) -> QueryCondition:
        """Filter roles having permission for entity type.

        Requires JOIN with ObjectPermissionRow.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ObjectPermissionRow.entity_type == entity_type

        return inner


class RoleOrders:
    """Query orders for roles."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RoleRow.name.asc()
        return RoleRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RoleRow.created_at.asc()
        return RoleRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RoleRow.updated_at.asc()
        return RoleRow.updated_at.desc()


class AssignedUserConditions:
    """Query conditions for assigned users."""

    @staticmethod
    def by_role_id(role_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRoleRow.role_id == role_id

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


class AssignedUserOrders:
    """Query orders for assigned users."""

    @staticmethod
    def username(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.username.asc()
        return UserRow.username.desc()

    @staticmethod
    def email(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.email.asc()
        return UserRow.email.desc()

    @staticmethod
    def granted_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRoleRow.granted_at.asc()
        return UserRoleRow.granted_at.desc()


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


class DomainScopeOrders:
    """Query orders for domain scope IDs."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DomainRow.name.asc()
        return DomainRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DomainRow.created_at.asc()
        return DomainRow.created_at.desc()


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


class ProjectScopeOrders:
    """Query orders for project (group) scope IDs."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return GroupRow.name.asc()
        return GroupRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return GroupRow.created_at.asc()
        return GroupRow.created_at.desc()


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


class UserScopeOrders:
    """Query orders for user scope IDs."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        """Order by username."""
        if ascending:
            return UserRow.username.asc()
        return UserRow.username.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.created_at.asc()
        return UserRow.created_at.desc()


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
