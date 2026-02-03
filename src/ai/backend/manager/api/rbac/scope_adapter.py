"""
Adapter for Scope API requests.
Handles conversion of request DTOs to BatchQuerier objects.
"""

from __future__ import annotations

from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.dto.manager.rbac.request import (
    ScopeFilter,
    ScopeOrder,
    SearchScopesRequest,
)
from ai.backend.common.dto.manager.rbac.response import ScopeDTO
from ai.backend.common.dto.manager.rbac.types import OrderDirection, ScopeOrderField
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.data.permission.types import ScopeData
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.permission_controller.options import (
    DomainScopeConditions,
    DomainScopeOrders,
    ProjectScopeConditions,
    ProjectScopeOrders,
    UserScopeConditions,
    UserScopeOrders,
)

__all__ = ("ScopeAdapter",)


class ScopeAdapter(BaseFilterAdapter):
    """Adapter for converting scope requests to BatchQuerier objects."""

    def build_querier(self, scope_type: ScopeType, request: SearchScopesRequest) -> BatchQuerier:
        """Build a BatchQuerier based on scope type."""
        match scope_type:
            case ScopeType.GLOBAL:
                return self._build_global_scope_querier(request)
            case ScopeType.DOMAIN:
                return self._build_domain_scope_querier(request)
            case ScopeType.PROJECT:
                return self._build_project_scope_querier(request)
            case ScopeType.USER:
                return self._build_user_scope_querier(request)
            case _:
                raise NotImplementedError(
                    "This adapter will be deprecated and search handlers will be implemented for each scope type"
                )

    def _build_domain_scope_querier(self, request: SearchScopesRequest) -> BatchQuerier:
        """Build a BatchQuerier for domain scopes from search request."""
        conditions = self._convert_domain_filter(request.filter) if request.filter else []
        orders = [self._convert_domain_order(o) for o in request.order] if request.order else []
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _build_project_scope_querier(self, request: SearchScopesRequest) -> BatchQuerier:
        """Build a BatchQuerier for project scopes from search request."""
        conditions = self._convert_project_filter(request.filter) if request.filter else []
        orders = [self._convert_project_order(o) for o in request.order] if request.order else []
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _build_user_scope_querier(self, request: SearchScopesRequest) -> BatchQuerier:
        """Build a BatchQuerier for user scopes from search request."""
        conditions = self._convert_user_filter(request.filter) if request.filter else []
        orders = [self._convert_user_order(o) for o in request.order] if request.order else []
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _build_global_scope_querier(self, request: SearchScopesRequest) -> BatchQuerier:
        """Build a BatchQuerier for global scope (no filtering needed)."""
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)
        return BatchQuerier(conditions=[], orders=[], pagination=pagination)

    def _convert_domain_filter(self, filter: ScopeFilter) -> list[QueryCondition]:
        """Convert scope filter to domain query conditions."""
        conditions: list[QueryCondition] = []

        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=DomainScopeConditions.by_name_contains,
                equals_factory=DomainScopeConditions.by_name_equals,
                starts_with_factory=DomainScopeConditions.by_name_starts_with,
                ends_with_factory=DomainScopeConditions.by_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions

    def _convert_project_filter(self, filter: ScopeFilter) -> list[QueryCondition]:
        """Convert scope filter to project query conditions."""
        conditions: list[QueryCondition] = []

        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=ProjectScopeConditions.by_name_contains,
                equals_factory=ProjectScopeConditions.by_name_equals,
                starts_with_factory=ProjectScopeConditions.by_name_starts_with,
                ends_with_factory=ProjectScopeConditions.by_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions

    def _convert_user_filter(self, filter: ScopeFilter) -> list[QueryCondition]:
        """Convert scope filter to user query conditions."""
        conditions: list[QueryCondition] = []

        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=UserScopeConditions.by_name_contains,
                equals_factory=UserScopeConditions.by_name_equals,
                starts_with_factory=UserScopeConditions.by_name_starts_with,
                ends_with_factory=UserScopeConditions.by_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions

    def _convert_domain_order(self, order: ScopeOrder) -> QueryOrder:
        """Convert scope order specification to domain query order."""
        ascending = order.direction == OrderDirection.ASC

        match order.field:
            case ScopeOrderField.NAME:
                return DomainScopeOrders.name(ascending=ascending)
            case ScopeOrderField.CREATED_AT:
                return DomainScopeOrders.created_at(ascending=ascending)

        raise ValueError(f"Unknown order field: {order.field}")

    def _convert_project_order(self, order: ScopeOrder) -> QueryOrder:
        """Convert scope order specification to project query order."""
        ascending = order.direction == OrderDirection.ASC

        match order.field:
            case ScopeOrderField.NAME:
                return ProjectScopeOrders.name(ascending=ascending)
            case ScopeOrderField.CREATED_AT:
                return ProjectScopeOrders.created_at(ascending=ascending)

        raise ValueError(f"Unknown order field: {order.field}")

    def _convert_user_order(self, order: ScopeOrder) -> QueryOrder:
        """Convert scope order specification to user query order."""
        ascending = order.direction == OrderDirection.ASC

        match order.field:
            case ScopeOrderField.NAME:
                return UserScopeOrders.name(ascending=ascending)
            case ScopeOrderField.CREATED_AT:
                return UserScopeOrders.created_at(ascending=ascending)

        raise ValueError(f"Unknown order field: {order.field}")

    def convert_to_dto(self, data: ScopeData) -> ScopeDTO:
        """Convert ScopeData to DTO.

        Args:
            data: Scope data from action result

        Returns:
            ScopeDTO for API response
        """
        return ScopeDTO(scope_type=data.id.scope_type, scope_id=data.id.scope_id, name=data.name)
