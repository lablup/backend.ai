"""Base adapter class for transport-agnostic service invocation."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationOptions,
    PaginationSpec,
    build_pagination,
)
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.entity_label.conditions import (
    EntityLabelConditions,
    EntityLabelNestedConditions,
)
from ai.backend.manager.models.specs.searcher import Searcher
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.filter_adapter import BaseFilterAdapter

if TYPE_CHECKING:
    from ai.backend.common.dto.manager.v2.entity_label.request import (
        EntityLabelFilter,
        EntityLabelNestedFilter,
    )
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

    def _convert_entity_label_filter(self, f: EntityLabelFilter) -> list[QueryCondition]:
        """Conditions matching a single label row.

        One instance narrows one row, so a `key` and a `value` given together constrain
        the same label rather than two different ones.
        """
        conditions: list[QueryCondition] = []
        if f.key is not None:
            condition = self.convert_string_filter(
                f.key,
                contains_factory=EntityLabelConditions.by_key_contains,
                equals_factory=EntityLabelConditions.by_key_equals,
                starts_with_factory=EntityLabelConditions.by_key_starts_with,
                ends_with_factory=EntityLabelConditions.by_key_ends_with,
                in_factory=EntityLabelConditions.by_key_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.value is not None:
            condition = self.convert_string_filter(
                f.value,
                contains_factory=EntityLabelConditions.by_value_contains,
                equals_factory=EntityLabelConditions.by_value_equals,
                starts_with_factory=EntityLabelConditions.by_value_starts_with,
                ends_with_factory=EntityLabelConditions.by_value_ends_with,
                in_factory=EntityLabelConditions.by_value_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.entity_type is not None:
            condition = self.convert_string_filter(
                f.entity_type,
                contains_factory=EntityLabelConditions.by_entity_type_contains,
                equals_factory=EntityLabelConditions.by_entity_type_equals,
                starts_with_factory=EntityLabelConditions.by_entity_type_starts_with,
                ends_with_factory=EntityLabelConditions.by_entity_type_ends_with,
                in_factory=EntityLabelConditions.by_entity_type_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.entity_id is not None:
            condition = self.convert_uuid_filter(
                f.entity_id,
                equals_factory=EntityLabelConditions.by_entity_id_equals,
                in_factory=EntityLabelConditions.by_entity_id_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_entity_label_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_entity_label_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_entity_label_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_entity_label_nested_filter(
        self, f: EntityLabelNestedFilter, nested: EntityLabelNestedConditions
    ) -> list[QueryCondition]:
        """Conditions selecting entities by the labels on them.

        Each relation compiles to one correlated EXISTS, so a relation's `key` and
        `value` land on the same label. Requiring two different labels is two relations
        combined by the entity filter's own AND.
        """
        conditions: list[QueryCondition] = []
        if f.some is not None:
            conditions.append(nested.some(self._convert_entity_label_filter(f.some)))
        if f.every is not None:
            conditions.append(nested.every(self._convert_entity_label_filter(f.every)))
        if f.none is not None:
            conditions.append(nested.none(self._convert_entity_label_filter(f.none)))
        return conditions

    def batch_load_failure(self, error: Exception | None) -> Exception | None:
        """What a DataLoader is handed for an id a bulk read returned no data for.

        An id matching no row stays ``None``; a denial is raised at the resolver
        awaiting it, so a caller is never told a row is missing when it is one they may
        not read.
        """
        if error is None or isinstance(error, EntityNotFoundError):
            return None
        return error

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
