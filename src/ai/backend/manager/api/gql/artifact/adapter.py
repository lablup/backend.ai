"""GraphQL adapters for converting artifact filters to repository queries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ai.backend.manager.api.gql.adapter import BaseGQLAdapter
from ai.backend.manager.repositories.base import (
    Querier,
    QueryCondition,
    QueryOrder,
    QueryPagination,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.artifact import (
        ArtifactFilter,
        ArtifactOrderBy,
        ArtifactRevisionFilter,
        ArtifactRevisionOrderBy,
    )

__all__ = (
    "ArtifactGQLAdapter",
    "ArtifactRevisionGQLAdapter",
)


class ArtifactGQLAdapter(BaseGQLAdapter):
    """Adapter for converting GraphQL artifact queries to repository Querier."""

    def build_querier(
        self,
        filter: Optional[ArtifactFilter] = None,
        order_by: Optional[list[ArtifactOrderBy]] = None,
        first: Optional[int] = None,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Querier:
        """Build Querier from GraphQL filter, order_by, and pagination."""
        conditions: list[QueryCondition] = []
        orders: list[QueryOrder] = []
        pagination: Optional[QueryPagination] = None

        if filter:
            conditions.extend(filter.build_conditions())

        if order_by:
            for order_spec in order_by:
                orders.append(order_spec.to_query_order())

        pagination = self.build_pagination(first, after, last, before, limit, offset)

        return Querier(conditions=conditions, orders=orders, pagination=pagination)


class ArtifactRevisionGQLAdapter(BaseGQLAdapter):
    """Adapter for converting GraphQL artifact revision queries to repository Querier."""

    def build_querier(
        self,
        filter: Optional[ArtifactRevisionFilter] = None,
        order_by: Optional[list[ArtifactRevisionOrderBy]] = None,
        first: Optional[int] = None,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Querier:
        """Build Querier from GraphQL filter, order_by, and pagination."""
        conditions: list[QueryCondition] = []
        orders: list[QueryOrder] = []
        pagination: Optional[QueryPagination] = None

        if filter:
            conditions.extend(filter.build_conditions())

        if order_by:
            for order_spec in order_by:
                orders.append(order_spec.to_query_order())

        pagination = self.build_pagination(first, after, last, before, limit, offset)

        return Querier(conditions=conditions, orders=orders, pagination=pagination)
