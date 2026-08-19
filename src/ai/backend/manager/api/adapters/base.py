"""Base adapter class for transport-agnostic service invocation."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationOptions,
    PaginationSpec,
    build_pagination,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.specs.searcher import Searcher
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.filter_adapter import BaseFilterAdapter

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
        methods; cursor and tiebreaker orders are taken from ``pagination_spec``.

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
        is_cursor_pagination = first is not None or last is not None

        all_conditions: list[QueryCondition] = []
        if base_conditions:
            all_conditions.extend(base_conditions)
        all_conditions.extend(conditions)

        all_orders: list[QueryOrder] = list(orders)
        if not all_orders and not is_cursor_pagination:
            all_orders.append(pagination_spec.forward_order)
        all_orders.append(pagination_spec.tiebreaker_order)

        pagination = build_pagination(
            PaginationOptions(
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            ),
            pagination_spec,
        )
        return BatchQuerier(conditions=all_conditions, orders=all_orders, pagination=pagination)

    def _build_searcher[TSearcher: Searcher[Any, Any]](
        self,
        searcher_class: type[TSearcher],
        conditions: list[QueryCondition],
        orders: list[QueryOrder],
        pagination_spec: PaginationSpec,
        first: int | None = None,
        after: str | None = None,
        last: int | None = None,
        before: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> TSearcher:
        """Build a domain :class:`Searcher` with the same pagination handling as
        :meth:`_build_querier`.

        A searcher carries the SELECT and the row conversion as well, so the ORM row
        never leaves the repository layer. Domains move here as they migrate;
        ``_build_querier`` goes away once the last one has.

        No ``base_conditions``: it was how a fixed filter — a foreign-key scope, mostly —
        got prepended before there was a scope to say it with. A scoped search now names
        its scopes on the action, so a caller reaching for this should be adding a
        ``OperationScope`` instead.
        """
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=pagination_spec,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
        return searcher_class(
            pagination=querier.pagination,
            conditions=querier.conditions,
            orders=querier.orders,
        )
