"""The standard operations against ``V2DBOpsProvider``, written once.

Every method is delegation; each spec carries the conversion, so no ORM row reaches
this class. Which spec goes with which operation: ``../KNOWLEDGE.md``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ai.backend.common.data.entity.types import (
    EntityData,
    EntityIdentifier,
    FieldIdentifier,
)
from ai.backend.manager.actions.v2.ops.result import BulkFieldOpsResult
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.creator import (
    EntityCreator,
    FieldCreator,
    GlobalEntityCreator,
    RoleManagedEntityCreator,
    SidecarCreator,
    SidecarFieldCreator,
)
from ai.backend.manager.models.specs.lookup import DataLookup, FieldOwnerLookup
from ai.backend.manager.models.specs.purger import (
    DataBatchPurger,
    EntityPurger,
    FieldPurger,
)
from ai.backend.manager.models.specs.querier import DataQuerier
from ai.backend.manager.models.specs.searcher import Searcher, SearcherResult
from ai.backend.manager.models.specs.types import BulkResultWithFailures, EntityWithFieldsResult
from ai.backend.manager.models.specs.updater import DataBatchUpdater, DataUpdater
from ai.backend.manager.models.specs.upserter import (
    EntityUpserter,
    FieldUpserter,
    GlobalEntityUpserter,
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

    async def field_owners(
        self, lookup: FieldOwnerLookup[Any, Any], field_ids: Sequence[FieldIdentifier]
    ) -> Mapping[FieldIdentifier, EntityIdentifier]:
        """Read the owning entity of each named field row; a row that is gone is absent."""
        async with self._ops.read_ops() as r:
            return await r.lookup_field_owners(lookup, field_ids)

    async def field_owner(
        self, lookup: FieldOwnerLookup[Any, Any], field_id: FieldIdentifier
    ) -> EntityIdentifier:
        """Read one field row's owning entity, raising if the row is gone.

        A lookup has to produce an id, so an absent row cannot be reported by returning
        ``None`` — the same contract ``lookup`` keeps.
        """
        owners = await self.field_owners(lookup, [field_id])
        owner = owners.get(field_id)
        if owner is None:
            raise EntityNotFoundError("No field row matches the given id")
        return owner

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

    async def create_global_entity_with_fields[TEntityData: EntityData, TFieldData](
        self,
        creator: GlobalEntityCreator[Any, TEntityData],
        field_creators: Sequence[FieldCreator[Any, Any, TFieldData]],
    ) -> EntityWithFieldsResult[TEntityData, TFieldData]:
        """Insert a global row and the field rows it owns, in one transaction.

        The owner id is not known until the parent row exists. The two writes share
        this session, so a failed field row takes the parent down with it.
        """
        async with self._ops.write_ops() as w:
            data = await w.create_global_entity(creator)
            fields = await w.atomic_create_field_entities(data.entity_id(), field_creators)
            return EntityWithFieldsResult(data=data, fields=fields)

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
        self, owner_id: Any, creator: FieldCreator[Any, Any, TData]
    ) -> TData:
        """Insert one field row under its owner's identifier."""
        async with self._ops.write_ops() as w:
            return await w.create_field_entity(owner_id, creator)

    async def atomic_create_global_entities(
        self, creators: Sequence[GlobalEntityCreator[Any, TData]]
    ) -> list[TData]:
        """Insert several global rows atomically; nothing is registered."""
        async with self._ops.write_ops() as w:
            return await w.atomic_create_global_entities(creators)

    async def atomic_create_entities(
        self, creators: Sequence[EntityCreator[Any, TData]]
    ) -> list[TData]:
        """Insert several entity rows atomically, provisioning each row's scope."""
        async with self._ops.write_ops() as w:
            return await w.atomic_create_entities(creators)

    async def atomic_create_role_managed_entities(
        self, creators: Sequence[RoleManagedEntityCreator[Any, TData]]
    ) -> list[TData]:
        """Insert several role-managed entity rows atomically, preset roles included."""
        async with self._ops.write_ops() as w:
            return await w.atomic_create_role_managed_entities(creators)

    async def atomic_create_field_entities(
        self, owner_id: Any, creators: Sequence[FieldCreator[Any, Any, TData]]
    ) -> list[TData]:
        """Insert several field rows sharing one owner, atomically."""
        async with self._ops.write_ops() as w:
            return await w.atomic_create_field_entities(owner_id, creators)

    async def create_sidecar(self, creator: SidecarCreator[Any, TData]) -> TData:
        async with self._ops.write_ops() as w:
            return await w.create_sidecar(creator)

    async def atomic_create_sidecars(
        self, creators: Sequence[SidecarCreator[Any, TData]]
    ) -> list[TData]:
        async with self._ops.write_ops() as w:
            return await w.atomic_create_sidecars(creators)

    async def atomic_create_sidecars_with_fields[TFieldData](
        self,
        creators: Sequence[SidecarCreator[Any, TData]],
        field_creators: Sequence[SidecarFieldCreator[Any, Any, TFieldData]],
    ) -> list[TData]:
        async with self._ops.write_ops() as w:
            return await w.atomic_create_sidecars_with_fields(creators, field_creators)

    async def purge_entity(self, purger: EntityPurger[Any, TData]) -> TData:
        """Hard-delete one entity row, tearing its scope down with it."""
        async with self._ops.write_ops() as w:
            data = await w.purge_entity(purger)
            if data is None:
                raise EntityNotFoundError(
                    f"{purger.row_class().__name__} {purger.pk_value()} not found"
                )
            return data

    async def purge_field_entity(self, purger: FieldPurger[Any, TData]) -> TData:
        """Hard-delete one field row; authorized through the owner, no membership work."""
        async with self._ops.write_ops() as w:
            data = await w.purge_field_entity(purger)
            if data is None:
                raise EntityNotFoundError(
                    f"{purger.row_class().__name__} {purger.pk_value()} not found"
                )
            return data

    async def partial_bulk_purge_entities(
        self, purgers: Mapping[EntityIdentifier, EntityPurger[Any, TData]]
    ) -> BulkResultWithFailures[TData]:
        """Hard-delete each named entity independently, answering for every one."""
        async with self._ops.write_ops() as w:
            return await w.partial_bulk_purge_entities(purgers)

    async def partial_bulk_purge_field_entities(
        self, purgers: Mapping[FieldIdentifier, FieldPurger[Any, TData]]
    ) -> BulkFieldOpsResult[TData]:
        """Hard-delete each named field row independently; authorized through the owner."""
        async with self._ops.write_ops() as w:
            return await w.partial_bulk_purge_field_entities(purgers)

    async def upsert_global_entity(self, upserter: GlobalEntityUpserter[Any, TData]) -> TData:
        """Insert or update a global row on conflict. Never absent."""
        async with self._ops.write_ops() as w:
            return await w.upsert_global_entity(upserter)

    async def upsert_entity(self, upserter: EntityUpserter[Any, TData]) -> TData:
        """Insert or update an entity row on conflict; the scope stays provisioned
        idempotently. Never absent."""
        async with self._ops.write_ops() as w:
            return await w.upsert_entity(upserter)

    async def atomic_upsert_global_entities(
        self, upserters: Sequence[GlobalEntityUpserter[Any, TData]]
    ) -> list[TData]:
        async with self._ops.write_ops() as w:
            return await w.atomic_upsert_global_entities(upserters)

    async def atomic_upsert_entities(
        self, upserters: Sequence[EntityUpserter[Any, TData]]
    ) -> list[TData]:
        async with self._ops.write_ops() as w:
            return await w.atomic_upsert_entities(upserters)

    async def upsert_field_entity(
        self, owner_id: Any, upserter: FieldUpserter[Any, Any, TData]
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

    async def partial_bulk_update(
        self, updaters: Mapping[EntityIdentifier, DataUpdater[Any, TData]]
    ) -> BulkResultWithFailures[TData]:
        """Update each named entity independently, answering for every one of them.

        Nothing is raised for an individual failure: the caller named these entities, so
        each one's fate belongs in the answer rather than aborting the rest.
        """
        async with self._ops.write_ops() as w:
            return await w.partial_bulk_update_data(updaters)

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
