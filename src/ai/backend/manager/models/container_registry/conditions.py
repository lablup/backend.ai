"""Query conditions for container registry rows."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.repositories.base import QueryCondition

from .row import ContainerRegistryRow


class ContainerRegistryConditions:
    """Query conditions for container registries."""

    @staticmethod
    def by_ids(registry_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ContainerRegistryRow.id.in_(registry_ids)

        return inner

    # --- registry_name string conditions ---

    @staticmethod
    def by_registry_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ContainerRegistryRow.registry_name) == spec.value.lower()
            else:
                condition = ContainerRegistryRow.registry_name == spec.value
            return ~condition if spec.negated else condition

        return inner

    @staticmethod
    def by_registry_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ContainerRegistryRow.registry_name.ilike(f"%{spec.value}%")
            else:
                condition = ContainerRegistryRow.registry_name.like(f"%{spec.value}%")
            return ~condition if spec.negated else condition

        return inner

    @staticmethod
    def by_registry_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ContainerRegistryRow.registry_name.ilike(f"{spec.value}%")
            else:
                condition = ContainerRegistryRow.registry_name.like(f"{spec.value}%")
            return ~condition if spec.negated else condition

        return inner

    @staticmethod
    def by_registry_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ContainerRegistryRow.registry_name.ilike(f"%{spec.value}")
            else:
                condition = ContainerRegistryRow.registry_name.like(f"%{spec.value}")
            return ~condition if spec.negated else condition

        return inner

    by_registry_name_in = staticmethod(make_string_in_factory(ContainerRegistryRow.registry_name))

    # --- type enum conditions ---

    @staticmethod
    def by_type_equals(type: ContainerRegistryType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ContainerRegistryRow.type == type

        return inner

    @staticmethod
    def by_type_not_equals(type: ContainerRegistryType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ContainerRegistryRow.type != type

        return inner

    @staticmethod
    def by_type_in(types: Collection[ContainerRegistryType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ContainerRegistryRow.type.in_(types)

        return inner

    @staticmethod
    def by_type_not_in(types: Collection[ContainerRegistryType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ContainerRegistryRow.type.not_in(types)

        return inner

    # --- is_global boolean condition ---

    @staticmethod
    def by_is_global(is_global: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ContainerRegistryRow.is_global.is_(is_global)

        return inner
