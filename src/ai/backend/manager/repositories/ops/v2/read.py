"""Read-only v2 ops: the data-returning query paths."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

import sqlalchemy as sa

from ai.backend.common.data.entity.types import (
    EntityIdentifier,
    EntityType,
    FieldData,
    FieldIdentifier,
    RuntimeEntityID,
)
from ai.backend.manager.errors.repository import (
    AmbiguousEntityKeyError,
    EmptyOperationScopeError,
)
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.lookup import (
    DataLookup,
    FieldKeyLookup,
    FieldOwnerKeyLookup,
    FieldOwnerLookup,
    RuntimeFieldOwnerLookup,
)
from ai.backend.manager.models.specs.querier import (
    BulkEntityQuerier,
    DataQuerier,
    FieldQuerier,
    OwnedFieldQuerier,
)
from ai.backend.manager.models.specs.searcher import Searcher, SearcherResult
from ai.backend.manager.repositories.ops.v2.base import V2OpsBase


class V2ReadOps(V2OpsBase):
    """Read-only operations bound to a single session; data-returning paths only."""

    async def current_time(self) -> datetime:
        """DB-sourced current time, consistent across servers (not a per-server clock)."""
        return (await self._sess.execute(sa.select(sa.func.now()))).scalar_one()

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

    async def query_bulk_data[TRow: Base, TData](
        self,
        querier: BulkEntityQuerier[TRow, TData],
        entity_ids: Sequence[EntityIdentifier],
    ) -> Mapping[EntityIdentifier, TData]:
        """Read the named entities, keyed by the ids the caller passed.

        An id matching no row is absent rather than an error: the caller decides
        whether that is a miss or one failed item among many.
        """
        if not entity_ids:
            return {}
        id_column = querier.entity_id_column()
        rows = (
            await self._sess.scalars(
                sa.select(querier.row_class()).where(id_column.in_(entity_ids))
            )
        ).all()
        found = {getattr(row, id_column.key): querier.to_data(row) for row in rows}
        return {entity_id: found[entity_id] for entity_id in entity_ids if entity_id in found}

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

    async def lookup_runtime_field_owners(
        self, lookup: RuntimeFieldOwnerLookup[Any], field_ids: Sequence[FieldIdentifier]
    ) -> Mapping[FieldIdentifier, RuntimeEntityID]:
        """Read the owning entity of each named field row whose owner is polymorphic.

        The counterpart of :meth:`lookup_field_owners` for the other lookup root: the
        query selects the owner's type third and the spec builds the identifier from it.
        Separate rather than branching, so a spec cannot reach the path that reads only
        the id and loses the kind.
        """
        if not field_ids:
            return {}
        rows = (await self._sess.execute(lookup.build_query(field_ids))).all()
        owners = {row[0]: lookup.owner_of(EntityType(row[2]), row[1]) for row in rows}
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

    async def lookup_field_by_key[TFieldID: FieldIdentifier, TOwnerID: EntityIdentifier](
        self, lookup: FieldKeyLookup[TFieldID, TOwnerID]
    ) -> tuple[TFieldID, TOwnerID] | None:
        """Read the field row the key names and the entity owning it; ``None`` if
        nothing matches."""
        rows = (await self._sess.execute(lookup.build_query().limit(2))).all()
        if not rows:
            return None
        if len(rows) > 1:
            raise AmbiguousEntityKeyError(
                "A field row key matched more than one row, so it is not a key."
            )
        return lookup.to_field_id(rows[0][0]), lookup.to_entity_id(rows[0][1])

    async def query_owned_fields[TOwnerID: EntityIdentifier, TRow: Base, TData: FieldData](
        self,
        querier: OwnedFieldQuerier[TOwnerID, TRow, TData],
        owner_ids: Sequence[TOwnerID],
    ) -> Mapping[TOwnerID, TData]:
        """Read the row each named entity designates, keyed by that entity.

        An owner designating nothing is absent from the mapping. A second row for the
        same owner is a fault rather than a pick: the querier's SELECT names one row,
        so two mean the narrowing is wrong or the constraint enforcing it is missing.
        """
        if not owner_ids:
            return {}
        owner_column = querier.owner_id_column()
        rows = (
            await self._sess.scalars(querier.build_select().where(owner_column.in_(owner_ids)))
        ).all()
        designated: dict[TOwnerID, TData] = {}
        for row in rows:
            owner_id = getattr(row, owner_column.key)
            if owner_id in designated:
                raise AmbiguousEntityKeyError(
                    f"{querier.__class__.__name__} matched more than one row for one owner."
                )
            designated[owner_id] = querier.to_data(row)
        return designated

    async def query_field_data[TRow: Base, TData: FieldData](
        self, querier: FieldQuerier[TRow, TData]
    ) -> TData | None:
        """Fetch one field row by its own id and return it as its ``data/`` type."""
        row_class = querier.row_class()
        result = await self._sess.execute(
            sa.select(row_class).where(querier.target_id_column() == querier.target_id_value())
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return querier.to_data(row)

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
