"""
Adapters to convert network DTOs to repository BatchQuerier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.dto.manager.network import (
    NetworkDTO,
    NetworkFilter,
    NetworkOrder,
    NetworkOrderField,
    OrderDirection,
    SearchNetworksRequest,
    UpdateNetworkRequest,
)
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.api.gql.base import StringMatchSpec, UUIDEqualMatchSpec, UUIDInMatchSpec
from ai.backend.manager.models.network.row import NetworkRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.base.updater import Updater, UpdaterSpec
from ai.backend.manager.types import OptionalState

__all__ = ("NetworkAdapter",)


@dataclass
class NetworkUpdaterSpec(UpdaterSpec[NetworkRow]):
    """UpdaterSpec for network updates."""

    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)

    @property
    @override
    def row_class(self) -> type[NetworkRow]:
        return NetworkRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        return to_update


class _NetworkConditions:
    """Query conditions for networks."""

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = NetworkRow.name.ilike(f"%{spec.value}%")
            else:
                condition = NetworkRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(NetworkRow.name) == spec.value.lower()
            else:
                condition = NetworkRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = NetworkRow.name.ilike(f"{spec.value}%")
            else:
                condition = NetworkRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = NetworkRow.name.ilike(f"%{spec.value}")
            else:
                condition = NetworkRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_driver_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = NetworkRow.driver.ilike(f"%{spec.value}%")
            else:
                condition = NetworkRow.driver.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_driver_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(NetworkRow.driver) == spec.value.lower()
            else:
                condition = NetworkRow.driver == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_driver_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = NetworkRow.driver.ilike(f"{spec.value}%")
            else:
                condition = NetworkRow.driver.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_driver_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = NetworkRow.driver.ilike(f"%{spec.value}")
            else:
                condition = NetworkRow.driver.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_project_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = NetworkRow.project == spec.value
            if spec.negated:
                condition = NetworkRow.project != spec.value
            return condition

        return inner

    @staticmethod
    def by_project_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return NetworkRow.project.not_in(spec.values)
            return NetworkRow.project.in_(spec.values)

        return inner

    @staticmethod
    def by_domain_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = NetworkRow.domain_name.ilike(f"%{spec.value}%")
            else:
                condition = NetworkRow.domain_name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(NetworkRow.domain_name) == spec.value.lower()
            else:
                condition = NetworkRow.domain_name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = NetworkRow.domain_name.ilike(f"{spec.value}%")
            else:
                condition = NetworkRow.domain_name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = NetworkRow.domain_name.ilike(f"%{spec.value}")
            else:
                condition = NetworkRow.domain_name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner


class _NetworkOrders:
    """Query orders for networks."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return NetworkRow.name.asc()
        return NetworkRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return NetworkRow.created_at.asc()
        return NetworkRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return NetworkRow.updated_at.asc()
        return NetworkRow.updated_at.desc()


class NetworkAdapter(BaseFilterAdapter):
    """Adapter for converting network requests to repository queries."""

    def convert_to_dto(self, row: NetworkRow) -> NetworkDTO:
        """Convert NetworkRow to DTO."""
        return NetworkDTO(
            id=row.id,
            name=row.name,
            ref_name=row.ref_name,
            driver=row.driver,
            options=dict(row.options),
            project=row.project,
            domain_name=row.domain_name,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def build_updater(self, request: UpdateNetworkRequest, network_id: UUID) -> Updater[NetworkRow]:
        """Convert update request to updater."""
        name = OptionalState[str].nop()

        if request.name is not None:
            name = OptionalState.update(request.name)

        updater_spec = NetworkUpdaterSpec(name=name)
        return Updater(spec=updater_spec, pk_value=network_id)

    def build_querier(self, request: SearchNetworksRequest) -> BatchQuerier:
        """Build a BatchQuerier for networks from search request."""
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(o) for o in request.order] if request.order else []
        pagination = self._build_pagination(request.limit, request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: NetworkFilter) -> list[QueryCondition]:
        """Convert network filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=_NetworkConditions.by_name_contains,
                equals_factory=_NetworkConditions.by_name_equals,
                starts_with_factory=_NetworkConditions.by_name_starts_with,
                ends_with_factory=_NetworkConditions.by_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.driver is not None:
            condition = self.convert_string_filter(
                filter.driver,
                contains_factory=_NetworkConditions.by_driver_contains,
                equals_factory=_NetworkConditions.by_driver_equals,
                starts_with_factory=_NetworkConditions.by_driver_starts_with,
                ends_with_factory=_NetworkConditions.by_driver_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.project is not None:
            condition = self.convert_uuid_filter(
                filter.project,
                equals_factory=_NetworkConditions.by_project_equals,
                in_factory=_NetworkConditions.by_project_in,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.domain_name is not None:
            condition = self.convert_string_filter(
                filter.domain_name,
                contains_factory=_NetworkConditions.by_domain_name_contains,
                equals_factory=_NetworkConditions.by_domain_name_equals,
                starts_with_factory=_NetworkConditions.by_domain_name_starts_with,
                ends_with_factory=_NetworkConditions.by_domain_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions

    def _convert_order(self, order: NetworkOrder) -> QueryOrder:
        """Convert network order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        if order.field == NetworkOrderField.NAME:
            return _NetworkOrders.name(ascending=ascending)
        if order.field == NetworkOrderField.CREATED_AT:
            return _NetworkOrders.created_at(ascending=ascending)
        if order.field == NetworkOrderField.UPDATED_AT:
            return _NetworkOrders.updated_at(ascending=ascending)
        raise ValueError(f"Unknown order field: {order.field}")

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)
