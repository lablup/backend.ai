"""Query conditions and orders for artifact repository."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactRemoteStatus,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_revision import ArtifactRevisionRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder


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


class ArtifactOrders:
    """Query orders for artifacts."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRow.name.asc()
        return ArtifactRow.name.desc()

    @staticmethod
    def type(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRow.type.asc()
        return ArtifactRow.type.desc()

    @staticmethod
    def scanned_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRow.scanned_at.asc()
        return ArtifactRow.scanned_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRow.updated_at.asc()
        return ArtifactRow.updated_at.desc()


class ArtifactRevisionConditions:
    """Query conditions for artifact revisions."""

    @staticmethod
    def by_ids(revision_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ArtifactRevisionRow.id.in_(revision_ids)

        return inner

    @staticmethod
    def by_artifact_id(artifact_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ArtifactRevisionRow.artifact_id == artifact_id

        return inner

    @staticmethod
    def by_version_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ArtifactRevisionRow.version.ilike(f"%{spec.value}%")
            else:
                condition = ArtifactRevisionRow.version.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_version_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ArtifactRevisionRow.version) == spec.value.lower()
            else:
                condition = ArtifactRevisionRow.version == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_version_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ArtifactRevisionRow.version.ilike(f"{spec.value}%")
            else:
                condition = ArtifactRevisionRow.version.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_version_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ArtifactRevisionRow.version.ilike(f"%{spec.value}")
            else:
                condition = ArtifactRevisionRow.version.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_statuses(statuses: list[ArtifactStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ArtifactRevisionRow.status.in_([s.value for s in statuses])

        return inner

    @staticmethod
    def by_remote_statuses(remote_statuses: list[ArtifactRemoteStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ArtifactRevisionRow.remote_status.in_([rs.value for rs in remote_statuses])

        return inner

    @staticmethod
    def by_size_greater_than(size: int) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ArtifactRevisionRow.size > size

        return inner

    @staticmethod
    def by_size_less_than(size: int) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ArtifactRevisionRow.size < size

        return inner

    @staticmethod
    def by_size_equals(size: int) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ArtifactRevisionRow.size == size

        return inner

    @staticmethod
    def by_size_not_equals(size: int) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ArtifactRevisionRow.size != size

        return inner

    @staticmethod
    def by_size_greater_than_or_equal(size: int) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ArtifactRevisionRow.size >= size

        return inner

    @staticmethod
    def by_size_less_than_or_equal(size: int) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ArtifactRevisionRow.size <= size

        return inner


class ArtifactRevisionOrders:
    """Query orders for artifact revisions."""

    @staticmethod
    def version(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRevisionRow.version.asc()
        return ArtifactRevisionRow.version.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRevisionRow.status.asc()
        return ArtifactRevisionRow.status.desc()

    @staticmethod
    def size(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRevisionRow.size.asc()
        return ArtifactRevisionRow.size.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRevisionRow.created_at.asc()
        return ArtifactRevisionRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRevisionRow.updated_at.asc()
        return ArtifactRevisionRow.updated_at.desc()
