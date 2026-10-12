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
<<<<<<< HEAD
from ai.backend.manager.api.rest.adapter import BaseFilterAdapter
from ai.backend.manager.repositories.base import BatchQuerier, QueryCondition, QueryOrder
=======
from ai.backend.manager.errors.base.not_found import NotFoundError
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import (
    combine_conditions_and,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.models.entity_label.searchable_fields import EntityLabelSearchableFields
from ai.backend.manager.models.specs.searcher import Searcher
from ai.backend.manager.repositories.base.filter_adapter import BaseFilterAdapter
from ai.backend.manager.repositories.base.querier import BatchQuerier
>>>>>>> 5bf2aa3e2 (fix(BA-8371): combine the fields of each OR filter item with AND (#15397))

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

<<<<<<< HEAD
    def __init__(self, processors: Processors) -> None:
        self._processors = processors
=======
    def _convert_entity_label_filter(self, f: EntityLabelFilter) -> list[QueryCondition]:
        """Conditions matching a single label row.

        One instance narrows one row, so a `key` and a `value` given together constrain
        the same label rather than two different ones.
        """
        fields = EntityLabelSearchableFields.own
        conditions = [
            *self.apply_string_filter(f.key, fields.key.filter),
            *self.apply_string_filter(f.value, fields.value.filter),
            *self.apply_string_filter(f.entity_type, fields.entity_type.filter),
            *self.apply_uuid_filter(f.entity_id, fields.entity_id.filter),
        ]
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_entity_label_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                sub_conditions = self._convert_entity_label_filter(sub)
                if sub_conditions:
                    or_conditions.append(combine_conditions_and(sub_conditions))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_entity_label_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    @overload
    async def batch_load_fields[TAction: BasePartialBulkFieldAction[Any, Any], TData, TNode](
        self,
        processor: PartialBulkFieldActionProcessor[TAction, TData],
        action: TAction,
        field_ids: Sequence[FieldIdentifier],
        to_node: Callable[[TData], TNode],
    ) -> list[TNode | Exception | None]: ...

    @overload
    async def batch_load_fields[
        TAction: BasePartialBulkOwnerCandidatesFieldAction[Any],
        TData,
        TNode,
    ](
        self,
        processor: PartialBulkOwnerCandidatesFieldActionProcessor[TAction, TData],
        action: TAction,
        field_ids: Sequence[FieldIdentifier],
        to_node: Callable[[TData], TNode],
    ) -> list[TNode | Exception | None]: ...

    async def batch_load_fields[TData, TNode](
        self,
        processor: PartialBulkFieldActionProcessor[Any, TData]
        | PartialBulkOwnerCandidatesFieldActionProcessor[Any, TData],
        action: Any,
        field_ids: Sequence[FieldIdentifier],
        to_node: Callable[[TData], TNode],
    ) -> list[TNode | Exception | None]:
        """One answer per named field row, in the given order, for a DataLoader.

        The node for a row that was read, ``None`` for an id matching no row, and the
        denial for a row whose owner the caller may not read. A batch naming no
        existing row at all is every id missing, not a failed run.
        """
        try:
            result: BulkFieldOpsResult[TData] = await processor.run(action)
        except NotFoundError:
            return [None for _ in field_ids]
        return [
            to_node(result.successes[field_id])
            if field_id in result.successes
            else self.batch_load_failure(result.errors.get(field_id))
            for field_id in field_ids
        ]

    def batch_load_failure(self, error: Exception | None) -> Exception | None:
        """What a DataLoader is handed for an id a bulk read returned no data for.

        An id matching no row stays ``None``; a denial is raised at the resolver
        awaiting it, so a caller is never told a row is missing when it is one they may
        not read.
        """
        if error is None or isinstance(error, NotFoundError):
            return None
        return error
>>>>>>> 5bf2aa3e2 (fix(BA-8371): combine the fields of each OR filter item with AND (#15397))

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
