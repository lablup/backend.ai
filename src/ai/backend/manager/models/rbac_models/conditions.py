"""Query conditions for RBAC models."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.filter_specs import (
    StringMatchSpec,
    UUIDEqualMatchSpec,
    UUIDInMatchSpec,
)
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.condition_utils import (
    make_string_in_factory,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.user import UserRow


class PermissionConditions:
    """Query conditions for permissions."""

    @staticmethod
    def by_entity_types(entity_types: list[EntityType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.entity_type.in_(entity_types)

        return inner

    @staticmethod
    def by_permissions(permissions: list[Permission]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.permission.in_(permissions)

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
    def by_role_id_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = UserRoleRow.role_id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_role_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = UserRoleRow.role_id.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_user_id_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = UserRoleRow.user_id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_user_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = UserRoleRow.user_id.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

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

    by_username_in = staticmethod(make_string_in_factory(UserRow.username))
    by_email_in = staticmethod(make_string_in_factory(UserRow.email))

    @staticmethod
    def by_granted_by_equals(granted_by: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRoleRow.granted_by == granted_by

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
