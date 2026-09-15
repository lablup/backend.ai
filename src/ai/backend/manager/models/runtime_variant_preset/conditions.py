"""Query conditions for runtime variant preset rows."""

from __future__ import annotations

import re
import uuid
from collections.abc import Collection
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import (
    StringMatchSpec,
    UUIDEqualMatchSpec,
    UUIDInMatchSpec,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import VERSION_PREFIX_PATTERN
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow

__all__ = ("RuntimeVariantPresetConditions",)


_VERSION_PREFIX = re.compile(VERSION_PREFIX_PATTERN)


def _version_segments(version: str) -> tuple[int, int, int] | None:
    """Read a version the way the row's generated columns read theirs."""
    prefix = _VERSION_PREFIX.match(version)
    if prefix is None:
        return None
    segments = [int(segment) for segment in prefix.group().split(".")]
    major, minor, patch = (segments + [0, 0, 0])[:3]
    return major, minor, patch


class RuntimeVariantPresetConditions:
    @staticmethod
    def by_ids(ids: Collection[UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RuntimeVariantPresetRow.id.in_(ids)

        return inner

    @staticmethod
    def by_runtime_variant_id(variant_id: UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RuntimeVariantPresetRow.runtime_variant == variant_id

        return inner

    @staticmethod
    def by_runtime_variant_id_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = RuntimeVariantPresetRow.runtime_variant == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_runtime_variant_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = RuntimeVariantPresetRow.runtime_variant.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = RuntimeVariantPresetRow.name.ilike(f"%{spec.value}%")
            else:
                condition = RuntimeVariantPresetRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(RuntimeVariantPresetRow.name) == spec.value.lower()
            else:
                condition = RuntimeVariantPresetRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = RuntimeVariantPresetRow.name.ilike(f"{spec.value}%")
            else:
                condition = RuntimeVariantPresetRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = RuntimeVariantPresetRow.name.ilike(f"%{spec.value}")
            else:
                condition = RuntimeVariantPresetRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_name_in = staticmethod(make_string_in_factory(RuntimeVariantPresetRow.name))

    @staticmethod
    def by_valid_at_version(version: str) -> QueryCondition:
        """Half-open range: ``added_version <= version < deprecated_version``."""
        target = _version_segments(version)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if target is None:
                return sa.false()
            major, minor, patch = target
            added = sa.tuple_(
                RuntimeVariantPresetRow.added_version_major,
                RuntimeVariantPresetRow.added_version_minor,
                RuntimeVariantPresetRow.added_version_patch,
            )
            deprecated = sa.tuple_(
                RuntimeVariantPresetRow.deprecated_version_major,
                RuntimeVariantPresetRow.deprecated_version_minor,
                RuntimeVariantPresetRow.deprecated_version_patch,
            )
            return sa.and_(
                sa.or_(
                    RuntimeVariantPresetRow.added_version.is_(None),
                    added <= sa.tuple_(sa.literal(major), sa.literal(minor), sa.literal(patch)),
                ),
                sa.or_(
                    RuntimeVariantPresetRow.deprecated_version.is_(None),
                    deprecated > sa.tuple_(sa.literal(major), sa.literal(minor), sa.literal(patch)),
                ),
            )

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Reads the cursor row's ``created_at`` and compares against that, because that is what
        the page is ordered by — comparing ids would draw the page boundary on a column the
        result is not sorted by.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(RuntimeVariantPresetRow.created_at)
                .where(RuntimeVariantPresetRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return RuntimeVariantPresetRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Reads the cursor row's ``created_at`` and compares against that, because that is what
        the page is ordered by — comparing ids would draw the page boundary on a column the
        result is not sorted by.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(RuntimeVariantPresetRow.created_at)
                .where(RuntimeVariantPresetRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return RuntimeVariantPresetRow.created_at > subquery

        return inner
