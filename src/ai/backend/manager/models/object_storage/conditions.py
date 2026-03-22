"""Query conditions for the object_storage domain."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.object_storage import ObjectStorageRow
from ai.backend.manager.repositories.base import QueryCondition


class ObjectStorageConditions:
    """QueryCondition factories for object storage filtering."""

    @staticmethod
    def by_ids(storage_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            return ObjectStorageRow.id.in_(storage_ids)

        return inner

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ObjectStorageRow.name.ilike(f"%{spec.value}%")
            else:
                condition = ObjectStorageRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ObjectStorageRow.name) == spec.value.lower()
            else:
                condition = ObjectStorageRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ObjectStorageRow.name.ilike(f"{spec.value}%")
            else:
                condition = ObjectStorageRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ObjectStorageRow.name.ilike(f"%{spec.value}")
            else:
                condition = ObjectStorageRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_host_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ObjectStorageRow.host.ilike(f"%{spec.value}%")
            else:
                condition = ObjectStorageRow.host.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_host_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ObjectStorageRow.host) == spec.value.lower()
            else:
                condition = ObjectStorageRow.host == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_host_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ObjectStorageRow.host.ilike(f"{spec.value}%")
            else:
                condition = ObjectStorageRow.host.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_host_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ObjectStorageRow.host.ilike(f"%{spec.value}")
            else:
                condition = ObjectStorageRow.host.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner
