"""The standard operations against ``V2DBOpsProvider``, written once.

A pass-through domain repository is the same methods every time — open a transaction,
hand the spec to ops, turn the row into its ``data/`` type. Two domains' ``search``
differ only in the class names. This is that layer with no domain code in it: construct
it with the v2 ops provider and it is ready, because each spec carries everything that
used to make the methods domain-specific, conversion included.

    | operation | spec                     | what it carries                        |
    |-----------|--------------------------|----------------------------------------|
    | get       | ``DataQuerier``          | row class, pk, ``to_data``             |
    | lookup    | ``DataLookup``           | row class, key conditions, ``to_data`` |
    | search    | ``Searcher``             | select, options, ``to_data``           |
    | create    | ``GlobalEntityCreator``  | family-split: the entity variant also  |
    |           | ``EntityCreator``        | provisions its scope + memberships     |
    |           | ``RoleManagedEntityCreator`` | entity + preset roles              |
    | update    | ``DataUpdater``          | row class, pk, values, ``to_data``     |
    | upsert    | ``EntityUpserter``       | conflict keys, scope kept provisioned  |
    | purge     | ``GlobalEntityPurger``   | family-split, symmetric with create    |
    |           | ``EntityPurger``         | entity: scope teardown included        |

The write specs are the v2 lineage (``models/specs/``): the create/purge/upsert
methods are split by membership family, so a scoped spec cannot flow through a
registration-free path — which family applies is visible at every call site.

Every method is delegation: the conversion runs inside the v2 ops, so no ORM row
reaches even this class. What is left here is the repository-layer seam — a missing
row becomes :class:`EntityNotFoundError` rather than ``None``.

There is no ``delete``: soft delete is a status transition whose column and values are
domain knowledge. A delete action carries a ``DataUpdater`` and runs through the
update path.

A domain that outgrows this — a branch, a multi-table write, its own not-found error —
writes a repository method as before.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.creator import (
    EntityCreator,
    FieldEntityCreator,
    GlobalEntityCreator,
    RoleManagedEntityCreator,
)
from ai.backend.manager.models.specs.lookup import DataLookup
from ai.backend.manager.models.specs.purger import (
    DataBatchPurger,
    EntityPurger,
    FieldEntityPurger,
    GlobalEntityPurger,
)
from ai.backend.manager.models.specs.querier import DataQuerier
from ai.backend.manager.models.specs.searcher import Searcher, SearcherResult
from ai.backend.manager.models.specs.types import BulkResultWithFailures
from ai.backend.manager.models.specs.updater import DataBatchUpdater, DataUpdater
from ai.backend.manager.models.specs.upserter import (
    EntityUpserter,
    FieldEntityUpserter,
    GlobalEntityUpserter,
    RoleManagedEntityUpserter,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider

__all__ = ("OpsRepository",)


class OpsRepository[TData]:
    """Ops-backed repository for one entity, parameterized only by its ``data/`` type.

    Takes nothing but the v2 ops provider: every spec names its own row class and
    carries its own conversion, so there is no domain state left to hold.
    """

    _ops: V2DBOpsProvider

    def __init__(self, ops_provider: V2DBOpsProvider) -> None:
        self._ops = ops_provider

    async def get(self, querier: DataQuerier[Any, TData]) -> TData:
        async with self._ops.read_ops() as r:
            data = await r.query_data(querier)
            if data is None:
                raise EntityNotFoundError(
                    f"{querier.row_class().__name__} {querier.pk_value()} not found"
                )
            return data

    async def lookup(self, lookup: DataLookup[Any, TData]) -> TData:
        """Read one entity by a non-primary key, raising if the key resolves to nothing.

        A lookup has to produce an id — its result contract says so — so an absent
        entity cannot be reported by returning ``None``.
        """
        async with self._ops.read_ops() as r:
            data = await r.lookup_data(lookup)
            if data is None:
                raise EntityNotFoundError(f"No {lookup.row_class().__name__} matches the given key")
            return data

    async def search_in_scopes(
        self,
        scopes: Sequence[OperationScope],
        searcher: Searcher[Any, TData],
    ) -> SearcherResult[TData]:
        """Read a page restricted to ``scopes``, which must not be empty.

        No fallback for an empty sequence: ops rejects one with
        ``EmptyOperationScopeError`` and that rejection is the point. A caller whose RBAC
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

    async def create_global_entity(self, creator: GlobalEntityCreator[Any, TData]) -> TData:
        async with self._ops.write_ops() as w:
            return await w.create_global_entity(creator)

    async def create_entity(self, creator: EntityCreator[Any, TData]) -> TData:
        """Insert one entity row; the write provisions its virtual scope and joins
        the declared memberships. No roles are involved on this path."""
        async with self._ops.write_ops() as w:
            return await w.create_entity(creator)

    async def create_role_managed_entity(
        self, creator: RoleManagedEntityCreator[Any, TData]
    ) -> TData:
        """Insert one role-managed entity row, additionally provisioning the roles
        its scope type's active presets call for."""
        async with self._ops.write_ops() as w:
            return await w.create_role_managed_entity(creator)

    async def create_field_entity(
        self, owner_id: Any, creator: FieldEntityCreator[Any, Any, TData]
    ) -> TData:
        """Insert one field row under its owner's identifier."""
        async with self._ops.write_ops() as w:
            return await w.create_field_entity(owner_id, creator)

    async def bulk_create_global_entities(
        self, creators: Sequence[GlobalEntityCreator[Any, TData]]
    ) -> list[TData]:
        """Insert several global rows atomically; nothing is registered."""
        async with self._ops.write_ops() as w:
            return await w.bulk_create_global_entities(creators)

    async def bulk_create_entities(
        self, creators: Sequence[EntityCreator[Any, TData]]
    ) -> list[TData]:
        """Insert several entity rows atomically, provisioning each row's scope."""
        async with self._ops.write_ops() as w:
            return await w.bulk_create_entities(creators)

    async def bulk_create_role_managed_entities(
        self, creators: Sequence[RoleManagedEntityCreator[Any, TData]]
    ) -> list[TData]:
        """Insert several role-managed entity rows atomically, preset roles included."""
        async with self._ops.write_ops() as w:
            return await w.bulk_create_role_managed_entities(creators)

    async def bulk_create_field_entities(
        self, owner_id: Any, creators: Sequence[FieldEntityCreator[Any, Any, TData]]
    ) -> list[TData]:
        """Insert several field rows sharing one owner, atomically."""
        async with self._ops.write_ops() as w:
            return await w.bulk_create_field_entities(owner_id, creators)

    async def purge_global_entity(self, purger: GlobalEntityPurger[Any, TData]) -> TData:
        async with self._ops.write_ops() as w:
            data = await w.purge_global_entity(purger)
            if data is None:
                raise EntityNotFoundError(
                    f"{purger.row_class().__name__} {purger.pk_value()} not found"
                )
            return data

    async def purge_entity(self, purger: EntityPurger[Any, TData]) -> TData:
        """Hard-delete one entity row, tearing its scope down with it."""
        async with self._ops.write_ops() as w:
            data = await w.purge_entity(purger)
            if data is None:
                raise EntityNotFoundError(
                    f"{purger.row_class().__name__} {purger.pk_value()} not found"
                )
            return data

    async def purge_field_entity(self, purger: FieldEntityPurger[Any, TData]) -> TData:
        """Hard-delete one field row; authorized through the owner, no membership work."""
        async with self._ops.write_ops() as w:
            data = await w.purge_field_entity(purger)
            if data is None:
                raise EntityNotFoundError(
                    f"{purger.row_class().__name__} {purger.pk_value()} not found"
                )
            return data

    async def bulk_purge_global_entities(
        self, purgers: Mapping[EntityID, GlobalEntityPurger[Any, TData]]
    ) -> BulkResultWithFailures[TData]:
        """Hard-delete each named global entity independently, answering for every one."""
        async with self._ops.write_ops() as w:
            return await w.bulk_purge_global_entities(purgers)

    async def bulk_purge_entities(
        self, purgers: Mapping[EntityID, EntityPurger[Any, TData]]
    ) -> BulkResultWithFailures[TData]:
        """Hard-delete each named entity independently, answering for every one."""
        async with self._ops.write_ops() as w:
            return await w.bulk_purge_entities(purgers)

    async def bulk_purge_field_entities(
        self, purgers: Mapping[EntityID, FieldEntityPurger[Any, TData]]
    ) -> BulkResultWithFailures[TData]:
        """Hard-delete each named field row independently; authorized through the owner."""
        async with self._ops.write_ops() as w:
            return await w.bulk_purge_field_entities(purgers)

    async def upsert_global_entity(self, upserter: GlobalEntityUpserter[Any, TData]) -> TData:
        """Insert or update a global row on conflict. Never absent."""
        async with self._ops.write_ops() as w:
            return await w.upsert_global_entity(upserter)

    async def upsert_entity(self, upserter: EntityUpserter[Any, TData]) -> TData:
        """Insert or update an entity row on conflict; the scope stays provisioned
        idempotently. Never absent."""
        async with self._ops.write_ops() as w:
            return await w.upsert_entity(upserter)

    async def upsert_role_managed_entity(
        self, upserter: RoleManagedEntityUpserter[Any, TData]
    ) -> TData:
        """Insert or update a role-managed entity row; preset roles are provisioned
        only when the upsert actually created the scope. Never absent."""
        async with self._ops.write_ops() as w:
            return await w.upsert_role_managed_entity(upserter)

    async def upsert_field_entity(
        self, owner_id: Any, upserter: FieldEntityUpserter[Any, Any, TData]
    ) -> TData:
        """Insert or update a field row on conflict, under its owner. Never absent."""
        async with self._ops.write_ops() as w:
            return await w.upsert_field_entity(owner_id, upserter)

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

    async def batch_update_in_scopes(
        self, scopes: Sequence[OperationScope], updater: DataBatchUpdater[Any, TData]
    ) -> list[TData]:
        """Update every matching row within ``scopes``, which must not be empty."""
        async with self._ops.write_ops() as w:
            return await w.batch_update_in_scopes(scopes, updater)

    async def batch_update_in_global(self, updater: DataBatchUpdater[Any, TData]) -> list[TData]:
        """Update every matching row across the table; caller holds the authority."""
        async with self._ops.write_ops() as w:
            return await w.batch_update_in_global(updater)

    async def batch_purge_in_scopes(
        self, scopes: Sequence[OperationScope], purger: DataBatchPurger[Any, TData]
    ) -> list[TData]:
        """Delete every selected row within ``scopes``, which must not be empty."""
        async with self._ops.write_ops() as w:
            return await w.batch_purge_in_scopes(scopes, purger)

    async def batch_purge_in_global(self, purger: DataBatchPurger[Any, TData]) -> list[TData]:
        """Delete every selected row across the table; caller holds the authority."""
        async with self._ops.write_ops() as w:
            return await w.batch_purge_in_global(purger)
