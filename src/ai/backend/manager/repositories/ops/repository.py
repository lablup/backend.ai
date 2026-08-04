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
    | create    | ``DataCreator``     | ``build_row``, ``to_data``            |
    | update    | ``DataUpdater``     | row class, pk, values, ``to_data``    |
    | upsert    | ``DataUpserter``    | row class, conflict keys, ``to_data`` |
    | purge     | ``DataPurger``      | row class, pk, checks, ``to_data``    |

Each write also has a many-row form — ``bulk_create`` over a sequence of ``DataCreator``,
``batch_update`` and ``batch_purge`` over a ``DataBatchUpdater`` / ``DataBatchPurger``.
They return what they wrote rather than a count, because a scope-shaped run reports the
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

from collections.abc import Sequence
from typing import Any

from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.manager.models.scopes import SearchScope
from ai.backend.manager.repositories.base.creator import DataCreator
from ai.backend.manager.repositories.base.purger import DataBatchPurger, DataPurger
from ai.backend.manager.repositories.base.querier import DataFinder, DataQuerier
from ai.backend.manager.repositories.base.searcher import Searcher, SearcherResult
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

    async def search(
        self,
        searcher: Searcher[Any, TData],
        scopes: Sequence[SearchScope],
    ) -> SearcherResult[TData]:
        """Read a page, scoped when ``scopes`` is non-empty.

        An empty sequence means an explicit global scan, which is why it routes to
        ``search_in_global`` rather than being rejected: the searcher reached here from
        an action that already declared it wanted no scope filter.
        """
        async with self._ops.read_ops() as r:
            if not scopes:
                return await r.search_in_global(searcher)
            return await r.search_with_scopes(scopes, searcher)

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
