"""Query conditions for artifact repository."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.data.artifact.types import ArtifactAvailability, ArtifactType
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.repositories.base import QueryCondition


class ArtifactConditions:
    """Query conditions for artifacts."""

    @staticmethod
    def by_ids(artifact_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ArtifactRow.id.in_(artifact_ids)

        return inner

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ArtifactRow.name.ilike(f"%{spec.value}%")
            else:
                condition = ArtifactRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ArtifactRow.name) == spec.value.lower()
            else:
                condition = ArtifactRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ArtifactRow.name.ilike(f"{spec.value}%")
            else:
                condition = ArtifactRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ArtifactRow.name.ilike(f"%{spec.value}")
            else:
                condition = ArtifactRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_registry_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ArtifactRow.registry_type.ilike(f"%{spec.value}%")
            else:
                condition = ArtifactRow.registry_type.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_registry_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ArtifactRow.registry_type) == spec.value.lower()
            else:
                condition = ArtifactRow.registry_type == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_registry_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ArtifactRow.registry_type.ilike(f"{spec.value}%")
            else:
                condition = ArtifactRow.registry_type.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_registry_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ArtifactRow.registry_type.ilike(f"%{spec.value}")
            else:
                condition = ArtifactRow.registry_type.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_source_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ArtifactRow.source_registry_type.ilike(f"%{spec.value}%")
            else:
                condition = ArtifactRow.source_registry_type.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_source_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ArtifactRow.source_registry_type) == spec.value.lower()
            else:
                condition = ArtifactRow.source_registry_type == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_source_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ArtifactRow.source_registry_type.ilike(f"{spec.value}%")
            else:
                condition = ArtifactRow.source_registry_type.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_source_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ArtifactRow.source_registry_type.ilike(f"%{spec.value}")
            else:
                condition = ArtifactRow.source_registry_type.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_types(types: list[ArtifactType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ArtifactRow.type.in_(types)

        return inner

    @staticmethod
    def by_availability(availability: list[ArtifactAvailability]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ArtifactRow.availability.in_([avail.value for avail in availability])

        return inner
