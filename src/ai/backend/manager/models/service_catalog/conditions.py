"""Query conditions for service catalog rows."""

from __future__ import annotations

from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.common.types import ServiceCatalogStatus
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.repositories.base import QueryCondition

from .row import ServiceCatalogRow


class ServiceCatalogConditions:
    """Query conditions for service catalog entries."""

    # --- service_group string conditions ---

    @staticmethod
    def by_service_group_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ServiceCatalogRow.service_group) == spec.value.lower()
            else:
                condition = ServiceCatalogRow.service_group == spec.value
            return ~condition if spec.negated else condition

        return inner

    @staticmethod
    def by_service_group_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ServiceCatalogRow.service_group.ilike(f"%{spec.value}%")
            else:
                condition = ServiceCatalogRow.service_group.like(f"%{spec.value}%")
            return ~condition if spec.negated else condition

        return inner

    @staticmethod
    def by_service_group_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ServiceCatalogRow.service_group.ilike(f"{spec.value}%")
            else:
                condition = ServiceCatalogRow.service_group.like(f"{spec.value}%")
            return ~condition if spec.negated else condition

        return inner

    @staticmethod
    def by_service_group_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ServiceCatalogRow.service_group.ilike(f"%{spec.value}")
            else:
                condition = ServiceCatalogRow.service_group.like(f"%{spec.value}")
            return ~condition if spec.negated else condition

        return inner

    by_service_group_in = staticmethod(make_string_in_factory(ServiceCatalogRow.service_group))

    # --- status enum conditions ---

    @staticmethod
    def by_status_equals(status: ServiceCatalogStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ServiceCatalogRow.status == status

        return inner

    @staticmethod
    def by_status_not_equals(status: ServiceCatalogStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ServiceCatalogRow.status != status

        return inner

    @staticmethod
    def by_status_in(statuses: Collection[ServiceCatalogStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ServiceCatalogRow.status.in_(statuses)

        return inner

    @staticmethod
    def by_status_not_in(statuses: Collection[ServiceCatalogStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ServiceCatalogRow.status.not_in(statuses)

        return inner
