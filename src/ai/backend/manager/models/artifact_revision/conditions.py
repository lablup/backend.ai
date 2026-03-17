"""Query conditions for artifact revision repository."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.data.artifact.types import ArtifactRemoteStatus, ArtifactStatus
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.repositories.base import QueryCondition


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
    def by_artifact_ids(artifact_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ArtifactRevisionRow.artifact_id.in_(artifact_ids)

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
