"""The standard operations against ``DBOpsProvider``, written once.

A pass-through domain repository is the same methods every time — open a transaction,
hand the spec to ops, turn the row into its ``data/`` type. Two domains' ``search``
differ only in the class names. This is that layer with no domain code in it: construct
it with the ops provider and it is ready, because each spec carries everything that used
to make the methods domain-specific, conversion included.

    | operation | spec                | what it carries                       |
    |-----------|---------------------|---------------------------------------|
    | get       | ``DataQuerier``     | row class, pk, ``to_data``            |
    | find      | ``DataFinder``      | row class, key conditions, ``to_data``|
    | search    | ``Searcher``        | select, options, ``to_data``          |
    |           |                     | scoped and global are separate calls  |
    | create    | ``DataCreator``     | ``build_row``, ``to_data``            |
    | update    | ``DataUpdater``     | row class, pk, values, ``to_data``    |
    | upsert    | ``DataUpserter``    | row class, conflict keys, ``to_data`` |
    | purge     | ``DataPurger``      | row class, pk, checks, ``to_data``    |

Each write also has many-row forms, and they differ in how failure lands:

- ``bulk_create`` over a sequence of ``DataCreator`` — one transaction, all or nothing.
- ``batch_update`` / ``batch_purge`` over a condition — one statement, all or nothing.
- ``bulk_update`` / ``bulk_purge`` over entities the caller named — each in its own
  savepoint, answering per entity, because the bulk shape reports per entity.

All of them return what they wrote rather than a count, because a run reports the
entities it touched through its result.

Every method is delegation: the conversion runs inside ``ReadOps``/``WriteOps``, so no
ORM row reaches even this class. What is left here is the repository-layer seam — a
missing row becomes :class:`EntityNotFoundError` rather than ``None``.

It carries no resilience policy. One shared across every entity could only label metrics
``ops_repository``, which says less than nothing about which entity was slow, and a retry
wrapped around a delegating method is a retry in the wrong place. Both belong on the ops
layer, where the transaction actually is.

There is no ``delete``: soft delete is a status transition whose column and values are
domain knowledge, and ``DBOpsProvider`` has no operation for it. A delete action carries
a ``DataUpdater`` and runs through the update path.

A domain that outgrows this — a branch, a multi-table write, its own not-found error —
writes a repository method as before. The two mix: the generic services take the
operation protocols in ``services/ops/repository.py``, which both satisfy.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.manager.models.scopes import SearchScope
from ai.backend.manager.repositories.base.creator import DataCreator
from ai.backend.manager.repositories.base.purger import DataBatchPurger, DataPurger
from ai.backend.manager.repositories.base.querier import DataFinder, DataQuerier
from ai.backend.manager.repositories.base.searcher import Searcher, SearcherResult
from ai.backend.manager.repositories.base.types import BulkResultWithFailures
from ai.backend.manager.repositories.base.updater import DataBatchUpdater, DataUpdater
from ai.backend.manager.repositories.base.upserter import DataUpserter
from ai.backend.manager.repositories.ops.base.provider import DBOpsProvider

__all__ = ("OpsRepository",)


class OpsRepository[TData]:
    """Ops-backed repository for one entity, parameterized only by its ``data/`` type.

    Takes nothing but the ops provider: every spec names its own row class and carries
    its own conversion, so there is no domain state left to hold.
    """

    _ops: DBOpsProvider

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._ops = ops_provider

    async def get(self, querier: DataQuerier[Any, TData]) -> TData:
        async with self._ops.read_ops() as r:
            data = await r.query_data(querier)
            if data is None:
                raise EntityNotFoundError(
                    f"{querier.row_class().__name__} {querier.pk_value()} not found"
                )
            return data

    async def find(self, finder: DataFinder[Any, TData]) -> TData:
        """Read one entity by a non-primary key, raising if the key resolves to nothing.

        A lookup has to produce an id — its result contract says so — so an absent
        entity cannot be reported by returning ``None``.
        """
        async with self._ops.read_ops() as r:
            data = await r.find_data(finder)
            if data is None:
                raise EntityNotFoundError(f"No {finder.row_class().__name__} matches the given key")
            return data

    async def search_in_scopes(
        self,
        scopes: Sequence[SearchScope],
        searcher: Searcher[Any, TData],
    ) -> SearcherResult[TData]:
        """Read a page restricted to ``scopes``, which must not be empty.

        No fallback for an empty sequence: ops rejects one with
        ``EmptySearchScopeError`` and that rejection is the point. A caller whose RBAC
        resolution came back empty is asking for nothing, not for everything, and
        widening it here would hand them every row.
        """
        async with self._ops.read_ops() as r:
            return await r.search_with_scopes(scopes, searcher)

    async def search_in_global(self, searcher: Searcher[Any, TData]) -> SearcherResult[TData]:
        """Read a page across the entire table, with no scope filter.

        A separate method rather than the empty case of the scoped one, matching the
        split ops itself makes: choosing this is an explicit decision that the caller
        holds the authority for it.
        """
        async with self._ops.read_ops() as r:
            return await r.search_in_global(searcher)

    async def create(self, creator: DataCreator[Any, TData]) -> TData:
        async with self._ops.write_ops() as w:
            return await w.create_data(creator)

    async def bulk_create(self, creators: Sequence[DataCreator[Any, TData]]) -> list[TData]:
        """Insert several rows atomically. Nothing is absent, so nothing to raise."""
        async with self._ops.write_ops() as w:
            return await w.bulk_create_data(creators)

    async def update(self, updater: DataUpdater[Any, TData]) -> TData:
        async with self._ops.write_ops() as w:
            data = await w.update_data(updater)
            if data is None:
                raise EntityNotFoundError(
                    f"{updater.row_class.__name__} {updater.pk_value()} not found"
                )
            return data

    async def bulk_update(
        self, updaters: Mapping[EntityID, DataUpdater[Any, TData]]
    ) -> BulkResultWithFailures[TData]:
        """Update each named entity independently, answering for every one of them.

        Nothing is raised for an individual failure: the caller named these entities, so
        each one's fate belongs in the answer rather than aborting the rest.
        """
        async with self._ops.write_ops() as w:
            return await w.bulk_update_data(updaters)

    async def bulk_purge(
        self, purgers: Mapping[EntityID, DataPurger[Any, TData]]
    ) -> BulkResultWithFailures[TData]:
        """Hard-delete each named entity independently, answering for every one."""
        async with self._ops.write_ops() as w:
            return await w.bulk_purge_data(purgers)

    async def batch_update(self, updater: DataBatchUpdater[Any, TData]) -> list[TData]:
        """Update every row matching the spec. An empty list means nothing matched."""
        async with self._ops.write_ops() as w:
            return await w.batch_update_data(updater)

    async def batch_purge(self, purger: DataBatchPurger[Any, TData]) -> list[TData]:
        """Delete every row the spec selects. An empty list means nothing matched."""
        async with self._ops.write_ops() as w:
            return await w.batch_purge_data(purger)

    async def upsert(self, upserter: DataUpserter[Any, TData]) -> TData:
        """Insert or update on conflict. Never absent, so nothing to raise."""
        async with self._ops.write_ops() as w:
            return await w.upsert_data(upserter)

    async def purge(self, purger: DataPurger[Any, TData]) -> TData:
        async with self._ops.write_ops() as w:
            data = await w.purge_data(purger)
            if data is None:
                raise EntityNotFoundError(
                    f"{purger.row_class().__name__} {purger.pk_value()} not found"
                )
            return data
