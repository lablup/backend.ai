"""Base adapter class for transport-agnostic service invocation."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationOptions,
    PaginationSpec,
    build_orders,
    build_pagination,
)
from ai.backend.manager.api.rest.adapter import BaseFilterAdapter
from ai.backend.manager.repositories.base import BatchQuerier, QueryCondition, QueryOrder

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


class BaseAdapter(BaseFilterAdapter):
    """Transport-agnostic adapter base.

    Accepts Pydantic DTOs, invokes Processor actions, returns Pydantic DTOs.
    Subclass per domain and implement concrete create/read/update/delete methods.

    Inherits ``BaseFilterAdapter`` for reusable StringFilter/UUIDFilter
    conversion utilities (``convert_string_filter``, ``convert_uuid_filter``).

    Adapters do NOT contain business logic — they translate between
    the DTO layer and the Processor/Action layer.
    """

    def __init__(self, processors: Processors) -> None:
        self._processors = processors

    def _build_querier(
        self,
        conditions: list[QueryCondition],
        orders: list[QueryOrder],
        pagination_spec: PaginationSpec,
        first: int | None = None,
        after: str | None = None,
        last: int | None = None,
        before: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        base_conditions: Sequence[QueryCondition] | None = None,
    ) -> BatchQuerier:
        """Build a BatchQuerier with cursor or offset pagination.

        Handles pagination mode selection (cursor forward/backward/offset/default)
        via the shared ``build_pagination()`` utility. Domain adapters supply
        pre-converted ``conditions`` and ``orders`` from their private conversion
        methods; cursor and tiebreaker orders are taken from ``pagination_spec``,
        and cursor pagination drops ``orders``.

        The optional ``base_conditions`` are prepended before ``conditions``
        (e.g., a foreign-key scope filter applied before user-supplied filters).

        Args:
            conditions: Filter conditions from the domain-specific converter.
            orders: Sort orders from the domain-specific converter.
            pagination_spec: Domain pagination configuration (cursor orders/factories).
            first: Cursor-forward page size.
            after: Cursor-forward start cursor.
            last: Cursor-backward page size.
            before: Cursor-backward end cursor.
            limit: Offset-based page size.
            offset: Offset-based page offset.
            base_conditions: Extra conditions prepended before ``conditions``.
        """
        options = PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )

        all_conditions: list[QueryCondition] = []
        if base_conditions:
            all_conditions.extend(base_conditions)
        all_conditions.extend(conditions)

        final_orders = build_orders(options, pagination_spec, orders)
        pagination = build_pagination(options, pagination_spec)
        return BatchQuerier(
            conditions=all_conditions,
            orders=final_orders,
            pagination=pagination,
        )
