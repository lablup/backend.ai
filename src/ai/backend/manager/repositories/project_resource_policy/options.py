from __future__ import annotations

import sqlalchemy as sa

from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder

__all__ = ("ProjectResourcePolicyConditions", "ProjectResourcePolicyOrders")


class ProjectResourcePolicyConditions:
    """Query conditions for project resource policies."""

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ProjectResourcePolicyRow.name.ilike(f"%{spec.value}%")
            else:
                condition = ProjectResourcePolicyRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ProjectResourcePolicyRow.name) == spec.value.lower()
            else:
                condition = ProjectResourcePolicyRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ProjectResourcePolicyRow.name.ilike(f"{spec.value}%")
            else:
                condition = ProjectResourcePolicyRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ProjectResourcePolicyRow.name.ilike(f"%{spec.value}")
            else:
                condition = ProjectResourcePolicyRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner


class ProjectResourcePolicyOrders:
    """Query orders for project resource policies."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ProjectResourcePolicyRow.name.asc()
        return ProjectResourcePolicyRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ProjectResourcePolicyRow.created_at.asc()
        return ProjectResourcePolicyRow.created_at.desc()
