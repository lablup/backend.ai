"""
Adapters to convert keypair DTOs to repository BatchQuerier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.dto.manager.keypair import (
    KeyPairDTO,
    KeyPairFilter,
    KeyPairOrder,
    KeyPairOrderField,
    OrderDirection,
    SearchKeyPairsRequest,
    UpdateKeyPairRequest,
)
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.base.updater import Updater, UpdaterSpec
from ai.backend.manager.types import OptionalState

__all__ = ("KeyPairAdapter",)


class KeyPairAdapter(BaseFilterAdapter):
    """Adapter for converting keypair requests to repository queries."""

    def convert_to_dto(self, data: KeyPairData) -> KeyPairDTO:
        """Convert KeyPairData to DTO."""
        return KeyPairDTO(
            access_key=str(data.access_key),
            secret_key=str(data.secret_key),
            user_id=None,
            user_uuid=data.user_id,
            is_active=data.is_active,
            is_admin=data.is_admin,
            created_at=data.created_at,
            modified_at=data.modified_at,
            last_used=None,
            resource_policy=data.resource_policy_name,
            rate_limit=data.rate_limit,
            num_queries=0,
        )

    def build_updater(self, request: UpdateKeyPairRequest, access_key: str) -> Updater[KeyPairRow]:
        """Convert update request to updater."""
        is_active = OptionalState[bool].nop()
        is_admin = OptionalState[bool].nop()
        resource_policy = OptionalState[str].nop()
        rate_limit = OptionalState[int].nop()

        if request.is_active is not None:
            is_active = OptionalState.update(request.is_active)
        if request.is_admin is not None:
            is_admin = OptionalState.update(request.is_admin)
        if request.resource_policy is not None:
            resource_policy = OptionalState.update(request.resource_policy)
        if request.rate_limit is not None:
            rate_limit = OptionalState.update(request.rate_limit)

        updater_spec = KeyPairUpdaterSpec(
            is_active=is_active,
            is_admin=is_admin,
            resource_policy=resource_policy,
            rate_limit=rate_limit,
        )
        return Updater(spec=updater_spec, pk_value=access_key)

    def build_querier(self, request: SearchKeyPairsRequest) -> BatchQuerier:
        """Build a BatchQuerier for keypairs from search request."""
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(o) for o in request.order] if request.order else []
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: KeyPairFilter) -> list[QueryCondition]:
        """Convert keypair filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        if filter.user_id is not None:
            condition = self.convert_string_filter(
                filter.user_id,
                contains_factory=KeyPairConditions.by_user_id_contains,
                equals_factory=KeyPairConditions.by_user_id_equals,
                starts_with_factory=KeyPairConditions.by_user_id_starts_with,
                ends_with_factory=KeyPairConditions.by_user_id_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.access_key is not None:
            condition = self.convert_string_filter(
                filter.access_key,
                contains_factory=KeyPairConditions.by_access_key_contains,
                equals_factory=KeyPairConditions.by_access_key_equals,
                starts_with_factory=KeyPairConditions.by_access_key_starts_with,
                ends_with_factory=KeyPairConditions.by_access_key_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.is_active is not None:
            conditions.append(KeyPairConditions.by_is_active(filter.is_active))

        if filter.is_admin is not None:
            conditions.append(KeyPairConditions.by_is_admin(filter.is_admin))

        if filter.resource_policy is not None:
            condition = self.convert_string_filter(
                filter.resource_policy,
                contains_factory=KeyPairConditions.by_resource_policy_contains,
                equals_factory=KeyPairConditions.by_resource_policy_equals,
                starts_with_factory=KeyPairConditions.by_resource_policy_starts_with,
                ends_with_factory=KeyPairConditions.by_resource_policy_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions

    def _convert_order(self, order: KeyPairOrder) -> QueryOrder:
        """Convert keypair order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        match order.field:
            case KeyPairOrderField.ACCESS_KEY:
                return KeyPairOrders.by_access_key(ascending=ascending)
            case KeyPairOrderField.CREATED_AT:
                return KeyPairOrders.by_created_at(ascending=ascending)
            case KeyPairOrderField.MODIFIED_AT:
                return KeyPairOrders.by_modified_at(ascending=ascending)
            case KeyPairOrderField.LAST_USED:
                return KeyPairOrders.by_last_used(ascending=ascending)
            case KeyPairOrderField.RATE_LIMIT:
                return KeyPairOrders.by_rate_limit(ascending=ascending)
            case KeyPairOrderField.NUM_QUERIES:
                return KeyPairOrders.by_num_queries(ascending=ascending)

        raise ValueError(f"Unknown order field: {order.field}")


@dataclass
class KeyPairUpdaterSpec(UpdaterSpec[KeyPairRow]):
    """UpdaterSpec for keypair updates."""

    is_active: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    is_admin: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    resource_policy: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    rate_limit: OptionalState[int] = field(default_factory=OptionalState[int].nop)

    @property
    @override
    def row_class(self) -> type[KeyPairRow]:
        return KeyPairRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.is_active.update_dict(to_update, "is_active")
        self.is_admin.update_dict(to_update, "is_admin")
        self.resource_policy.update_dict(to_update, "resource_policy")
        self.rate_limit.update_dict(to_update, "rate_limit")
        return to_update


class KeyPairConditions:
    """Query conditions for keypair filters."""

    @staticmethod
    def by_user_id_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = KeyPairRow.user_id.ilike(f"%{spec.value}%")
            else:
                condition = KeyPairRow.user_id.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_user_id_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(KeyPairRow.user_id) == spec.value.lower()
            else:
                condition = KeyPairRow.user_id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_user_id_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = KeyPairRow.user_id.ilike(f"{spec.value}%")
            else:
                condition = KeyPairRow.user_id.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_user_id_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = KeyPairRow.user_id.ilike(f"%{spec.value}")
            else:
                condition = KeyPairRow.user_id.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_access_key_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = KeyPairRow.access_key.ilike(f"%{spec.value}%")
            else:
                condition = KeyPairRow.access_key.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_access_key_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(KeyPairRow.access_key) == spec.value.lower()
            else:
                condition = KeyPairRow.access_key == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_access_key_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = KeyPairRow.access_key.ilike(f"{spec.value}%")
            else:
                condition = KeyPairRow.access_key.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_access_key_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = KeyPairRow.access_key.ilike(f"%{spec.value}")
            else:
                condition = KeyPairRow.access_key.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_is_active(is_active: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KeyPairRow.is_active == is_active

        return inner

    @staticmethod
    def by_is_admin(is_admin: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KeyPairRow.is_admin == is_admin

        return inner

    @staticmethod
    def by_resource_policy_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = KeyPairRow.resource_policy.ilike(f"%{spec.value}%")
            else:
                condition = KeyPairRow.resource_policy.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_policy_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(KeyPairRow.resource_policy) == spec.value.lower()
            else:
                condition = KeyPairRow.resource_policy == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_policy_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = KeyPairRow.resource_policy.ilike(f"{spec.value}%")
            else:
                condition = KeyPairRow.resource_policy.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_policy_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = KeyPairRow.resource_policy.ilike(f"%{spec.value}")
            else:
                condition = KeyPairRow.resource_policy.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner


class KeyPairOrders:
    """Query orders for keypair sorting."""

    @staticmethod
    def by_access_key(ascending: bool = True) -> QueryOrder:
        col = KeyPairRow.access_key
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_created_at(ascending: bool = True) -> QueryOrder:
        col = KeyPairRow.created_at
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_modified_at(ascending: bool = True) -> QueryOrder:
        col = KeyPairRow.modified_at
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_last_used(ascending: bool = True) -> QueryOrder:
        col = KeyPairRow.last_used
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_rate_limit(ascending: bool = True) -> QueryOrder:
        col = KeyPairRow.rate_limit
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_num_queries(ascending: bool = True) -> QueryOrder:
        col = KeyPairRow.num_queries
        return col.asc() if ascending else col.desc()
