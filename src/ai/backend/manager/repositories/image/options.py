"""Query conditions and orders for image repository."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.data.image.types import ImageStatus
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder


class ImageConditions:
    """Query conditions for images."""

    @staticmethod
    def by_ids(image_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ImageRow.id.in_(image_ids)

        return inner

    @staticmethod
    def by_canonicals(canonicals: Collection[str]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ImageRow.name.in_(canonicals)

        return inner

    @staticmethod
    def by_statuses(statuses: Collection[ImageStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ImageRow.status.in_(statuses)

        return inner

    @staticmethod
    def by_architecture(architecture: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ImageRow.architecture == architecture

        return inner

    @staticmethod
    def by_registry_id(registry_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ImageRow.registry_id == registry_id

        return inner

    # String filter factories for name
    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ImageRow.name.ilike(f"%{spec.value}%")
            else:
                condition = ImageRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ImageRow.name) == spec.value.lower()
            else:
                condition = ImageRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ImageRow.name.ilike(f"{spec.value}%")
            else:
                condition = ImageRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ImageRow.name.ilike(f"%{spec.value}")
            else:
                condition = ImageRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # String filter factories for architecture
    @staticmethod
    def by_architecture_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ImageRow.architecture.ilike(f"%{spec.value}%")
            else:
                condition = ImageRow.architecture.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_architecture_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ImageRow.architecture) == spec.value.lower()
            else:
                condition = ImageRow.architecture == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_architecture_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ImageRow.architecture.ilike(f"{spec.value}%")
            else:
                condition = ImageRow.architecture.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_architecture_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ImageRow.architecture.ilike(f"%{spec.value}")
            else:
                condition = ImageRow.architecture.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner


class ImageOrders:
    """Query orders for images."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ImageRow.name.asc()
        return ImageRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ImageRow.created_at.asc()
        return ImageRow.created_at.desc()
