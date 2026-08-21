"""Read-only v2 ops: the data-returning query paths."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier, FieldIdentifier
from ai.backend.manager.errors.repository import (
    AmbiguousEntityKeyError,
    EmptyOperationScopeError,
)
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.lookup import (
    DataLookup,
    FieldOwnerKeyLookup,
    FieldOwnerLookup,
)
from ai.backend.manager.models.specs.querier import DataQuerier
from ai.backend.manager.models.specs.searcher import Searcher, SearcherResult
from ai.backend.manager.repositories.ops.v2.base import V2OpsBase


class V2ReadOps(V2OpsBase):
    """Read-only operations bound to a single session; data-returning paths only."""

    async def query_data[TRow: Base, TData](
        self, querier: DataQuerier[TRow, TData]
    ) -> TData | None:
        """Fetch a single row by primary key and return it as its ``data/`` type."""
        row_class = querier.row_class()
        result = await self._sess.execute(
            sa.select(row_class).where(querier.entity_id_column() == querier.entity_id_value())
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return querier.to_data(row)

    async def lookup_entity_id[TRow: Base, TEntityID: EntityIdentifier](
        self, lookup: DataLookup[TRow, TEntityID]
    ) -> TEntityID | None:
        """Resolve a key that is not a primary key into the id of the entity it names.

        Reads at most two rows and rejects the second: a lookup key is expected to
        be unique, so more than one match means the conditions are wrong or the
        constraint that should enforce it is missing.
        """
        row_class = lookup.row_class()
        query = sa.select(row_class)
        for condition in lookup.conditions():
            query = query.where(condition())
        result = await self._sess.execute(query.limit(2))
        rows = result.scalars().all()
        if not rows:
            return None
        if len(rows) > 1:
            raise AmbiguousEntityKeyError(
                f"The given key matches more than one {row_class.__name__}"
            )
        return lookup.to_entity_id(rows[0])

    async def lookup_field_owners(
        self, lookup: FieldOwnerLookup[Any, Any], field_ids: Sequence[FieldIdentifier]
    ) -> Mapping[FieldIdentifier, EntityIdentifier]:
        """Read the owning entity of each named field row.

        A row that is gone is absent from the mapping rather than an error: the caller
        decides whether that is a miss or one failed item among many.
        """
        if not field_ids:
            return {}
        rows = (await self._sess.execute(lookup.build_query(field_ids))).all()
        owners = {row[0]: lookup.to_entity_id(row[1]) for row in rows}
        return {field_id: owners[field_id] for field_id in field_ids if field_id in owners}

    async def lookup_field_owner_by_key[TOwnerID: EntityIdentifier](
        self, lookup: FieldOwnerKeyLookup[TOwnerID]
    ) -> TOwnerID | None:
        """Read the entity owning the field row the key names; ``None`` if nothing matches."""
        rows = (await self._sess.execute(lookup.build_query().limit(2))).all()
        if not rows:
            return None
        if len(rows) > 1:
            raise AmbiguousEntityKeyError(
                "A field owner key matched more than one row, so it is not a key."
            )
        return lookup.to_entity_id(rows[0][0])

    async def search_with_scopes[TRow: Base, TData](
        self,
        scopes: Sequence[OperationScope],
        searcher: Searcher[TRow, TData],
    ) -> SearcherResult[TData]:
        """Run a searcher restricted to the given scopes; at least one is required."""
        if not scopes:
            raise EmptyOperationScopeError(
                "search_with_scopes requires at least one scope; "
                "use search_in_global for an explicit unscoped global search."
            )
        return await self._search(scopes, searcher)

    async def search_in_global[TRow: Base, TData](
        self,
        searcher: Searcher[TRow, TData],
    ) -> SearcherResult[TData]:
        """Run a searcher across the entire table, with NO scope filter.

        Permitted only for callers that already hold full authority — superadmin
        endpoints or internal system operations.
        """
        return await self._search((), searcher)

    async def _search[TRow: Base, TData](
        self,
        scopes: Sequence[OperationScope],
        searcher: Searcher[TRow, TData],
    ) -> SearcherResult[TData]:
        """Run the searcher's SELECT with its conditions, orders, and pagination.

        Scope conditions form a single OR group AND-merged with the searcher's own
        conditions; each scope's existence checks are validated first.
        """
        query = searcher.build_select()
        count_query = sa.select(sa.func.count()).select_from(query.froms[0])
        if scopes:
            await self._validate_scope_existence(scopes)
            scope_clause = self._scopes_condition(scopes)
            query = query.where(scope_clause)
            count_query = count_query.where(scope_clause)
        for condition in searcher.conditions:
            query = query.where(condition())
            count_query = count_query.where(condition())
        # Pagination applies its own default order (cursor pagination includes the
        # cursor condition); the searcher's orders follow as secondary criteria.
        query = searcher.pagination.apply(query)
        for order in searcher.orders:
            query = query.order_by(order)
        rows = list((await self._sess.execute(searcher.pagination.attach_count(query))).all())
        total_count = searcher.pagination.count_from_rows(rows)
        if total_count is None:
            # Strategy could not derive the count from rows: run the count query.
            total_count = (await self._sess.execute(count_query)).scalar() or 0
        page_info = searcher.pagination.compute_page_info(rows, total_count)
        return SearcherResult(
            # build_select selects a single entity, so the row's first element is TRow.
            items=[searcher.to_data(row[0]) for row in page_info.rows],
            total_count=total_count,
            has_next_page=page_info.has_next_page,
            has_previous_page=page_info.has_previous_page,
        )
