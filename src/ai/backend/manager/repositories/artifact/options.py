"""Query conditions and orders for artifact repository."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

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
    def by_name_contains(name: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return ArtifactRow.name.ilike(f"%{name}%")
            else:
                return ArtifactRow.name.like(f"%{name}%")

        return inner

    @staticmethod
    def by_name_equals(name: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(ArtifactRow.name) == name.lower()
            else:
                return ArtifactRow.name == name

        return inner

    @staticmethod
    def by_registry_contains(registry: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return ArtifactRow.registry_type.ilike(f"%{registry}%")
            else:
                return ArtifactRow.registry_type.like(f"%{registry}%")

        return inner

    @staticmethod
    def by_registry_equals(registry: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(ArtifactRow.registry_type) == registry.lower()
            else:
                return ArtifactRow.registry_type == registry

        return inner

    @staticmethod
    def by_source_contains(source: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return ArtifactRow.source_registry_type.ilike(f"%{source}%")
            else:
                return ArtifactRow.source_registry_type.like(f"%{source}%")

        return inner

    @staticmethod
    def by_source_equals(source: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(ArtifactRow.source_registry_type) == source.lower()
            else:
                return ArtifactRow.source_registry_type == source

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
        else:
            return ArtifactRow.name.desc()

    @staticmethod
    def type(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRow.type.asc()
        else:
            return ArtifactRow.type.desc()

    @staticmethod
    def scanned_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRow.scanned_at.asc()
        else:
            return ArtifactRow.scanned_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRow.updated_at.asc()
        else:
            return ArtifactRow.updated_at.desc()


class ArtifactRevisionConditions:
    """Query conditions for artifact revisions."""

    @staticmethod
    def by_ids(revision_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ArtifactRevisionRow.id.in_(revision_ids)

        return inner

    @staticmethod
    def by_version_contains(version: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return ArtifactRevisionRow.version.ilike(f"%{version}%")
            else:
                return ArtifactRevisionRow.version.like(f"%{version}%")

        return inner

    @staticmethod
    def by_version_equals(version: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(ArtifactRevisionRow.version) == version.lower()
            else:
                return ArtifactRevisionRow.version == version

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
        else:
            return ArtifactRevisionRow.version.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRevisionRow.status.asc()
        else:
            return ArtifactRevisionRow.status.desc()

    @staticmethod
    def size(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRevisionRow.size.asc()
        else:
            return ArtifactRevisionRow.size.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRevisionRow.created_at.asc()
        else:
            return ArtifactRevisionRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRevisionRow.updated_at.asc()
        else:
            return ArtifactRevisionRow.updated_at.desc()
