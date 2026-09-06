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
    FieldData,
    FieldIdentifier,
    RuntimeEntityID,
)
from ai.backend.manager.actions.v2.ops.result import BulkFieldOpsResult
from ai.backend.manager.errors.repository import EntityNotFoundError, EntityWriteRefusedError
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.creator import (
    DanglingFieldCreator,
    EntityCreator,
    FieldCreator,
    FieldToCreate,
    GlobalEntityCreator,
    NestedFieldCreator,
    RoleManagedEntityCreator,
    RoleManagedGlobalEntityCreator,
)
from ai.backend.manager.models.specs.lookup import (
    DataLookup,
    FieldKeyLookup,
    FieldOwnerKeyLookup,
    FieldOwnerLookup,
    RuntimeFieldOwnerLookup,
)
from ai.backend.manager.models.specs.purger import (
    EntityBatchPurger,
    EntityPurger,
    FieldPurger,
)
from ai.backend.manager.models.specs.querier import (
    BulkEntityQuerier,
    DataQuerier,
    FieldQuerier,
    OwnedFieldQuerier,
)
from ai.backend.manager.models.specs.searcher import Searcher, SearcherResult
from ai.backend.manager.models.specs.types import BulkResultWithFailures, EntityWithFieldsResult
from ai.backend.manager.models.specs.updater import (
    DataBatchUpdater,
    DataUpdater,
    GuardedDataUpdater,
)
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
                    f"{querier.row_class().__name__} {querier.entity_id_value()} not found"
                )
            return data

    async def bulk_get(
        self, querier: BulkEntityQuerier[Any, TData], entity_ids: Sequence[EntityIdentifier]
    ) -> Mapping[EntityIdentifier, TData]:
        """Read the named entities; one that is gone is absent instead of raising.

        Unlike :meth:`get`, the run answers for each id separately, so a missing row is
        one failed item rather than a failed run.
        """
        async with self._ops.read_ops() as r:
            return await r.query_bulk_data(querier, entity_ids)

    async def get_field[TFieldData: FieldData](
        self, querier: FieldQuerier[Any, TFieldData]
    ) -> TFieldData:
        """Read one field row by its own id, raising if it is gone."""
        async with self._ops.read_ops() as r:
            data = await r.query_field_data(querier)
            if data is None:
                raise EntityNotFoundError(
                    f"{querier.row_class().__name__} {querier.target_id_value()} not found"
                )
            return data

    async def lookup[TEntityID: EntityIdentifier](
        self, lookup: DataLookup[Any, TEntityID]
    ) -> TEntityID:
        """Resolve a non-primary key into the id it names, raising if it names nothing.

        A lookup has to produce an id — its result contract says so — so an absent
        entity cannot be reported by returning ``None``.
        """
        async with self._ops.read_ops() as r:
            entity_id = await r.lookup_entity_id(lookup)
            if entity_id is None:
                raise EntityNotFoundError(f"No {lookup.row_class().__name__} matches the given key")
            return entity_id

    async def owned_fields[TOwnerID: EntityIdentifier, TFieldData: FieldData](
        self,
        querier: OwnedFieldQuerier[TOwnerID, Any, TFieldData],
        owner_ids: Sequence[TOwnerID],
    ) -> Mapping[TOwnerID, TFieldData]:
        """Read the row each named entity designates; an owner designating nothing is absent."""
        async with self._ops.read_ops() as r:
            return await r.query_owned_fields(querier, owner_ids)

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

    async def runtime_field_owners(
        self, lookup: RuntimeFieldOwnerLookup[Any], field_ids: Sequence[FieldIdentifier]
    ) -> Mapping[FieldIdentifier, RuntimeEntityID]:
        """Read the polymorphic owning entity of each named field row."""
        async with self._ops.read_ops() as r:
            return await r.lookup_runtime_field_owners(lookup, field_ids)

    async def runtime_field_owner(
        self, lookup: RuntimeFieldOwnerLookup[Any], field_id: FieldIdentifier
    ) -> RuntimeEntityID:
        """Read one field row's polymorphic owning entity, raising if the row is gone."""
        owners = await self.runtime_field_owners(lookup, [field_id])
        owner = owners.get(field_id)
        if owner is None:
            raise EntityNotFoundError("No field row matches the given id")
        return owner

    async def field_owner_by_key[TOwnerID: EntityIdentifier](
        self, lookup: FieldOwnerKeyLookup[TOwnerID]
    ) -> TOwnerID:
        """Read the owner the key names, raising if nothing matches.

        A lookup has to produce an id, so an absent row cannot be reported by returning
        ``None`` — the same contract the other lookups keep.
        """
        async with self._ops.read_ops() as r:
            owner = await r.lookup_field_owner_by_key(lookup)
        if owner is None:
            raise EntityNotFoundError("No field row matches the given key")
        return owner

    async def field_by_key[TFieldID: FieldIdentifier, TOwnerID: EntityIdentifier](
        self, lookup: FieldKeyLookup[TFieldID, TOwnerID]
    ) -> tuple[TFieldID, TOwnerID]:
        """Read the field row the key names and its owner, raising if nothing matches.

        A lookup has to produce an id, so an absent row cannot be reported by returning
        ``None`` — the same contract the other lookups keep.
        """
        async with self._ops.read_ops() as r:
            resolved = await r.lookup_field_by_key(lookup)
        if resolved is None:
            raise EntityNotFoundError("No field row matches the given key")
        return resolved

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

    async def create_global_entity_with_fields[TEntityData: EntityData, TFieldData: FieldData](
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
        """Insert one entity row; the write provisions its virtual entity and joins
        the declared memberships. No roles are involved on this path."""
        async with self._ops.write_ops() as w:
            return await w.create_entity(creator)

    async def create_entity_with_fields[TEntityData: EntityData, TFieldData: FieldData](
        self,
        creator: EntityCreator[Any, TEntityData],
        field_creators: Sequence[FieldCreator[Any, Any, TFieldData]],
    ) -> EntityWithFieldsResult[TEntityData, TFieldData]:
        """Insert an entity row and the field rows it owns, in one transaction.

        The owner id is not known until the parent row exists. The two writes share
        this session, so a failed field row takes the parent down with it.
        """
        async with self._ops.write_ops() as w:
            data = await w.create_entity(creator)
            fields = await w.atomic_create_field_entities(data.entity_id(), field_creators)
            return EntityWithFieldsResult(data=data, fields=fields)

    async def create_role_managed_global_entity(
        self, creator: RoleManagedGlobalEntityCreator[Any, TData]
    ) -> TData:
        """Insert one role-managed row created in no scope, preset roles included."""
        async with self._ops.write_ops() as w:
            return await w.create_role_managed_global_entity(creator)

    async def create_role_managed_entity(
        self, creator: RoleManagedEntityCreator[Any, TData]
    ) -> TData:
        """Insert one role-managed entity row, owned and governed by the scopes it is
        created in, preset roles included."""
        async with self._ops.write_ops() as w:
            return await w.create_role_managed_entity(creator)

    async def create_field[TFieldData: FieldData](
        self, owner_id: Any, creator: FieldCreator[Any, Any, TFieldData]
    ) -> TFieldData:
        """Insert one field row under its owner's identifier."""
        async with self._ops.write_ops() as w:
            return await w.create_field(owner_id, creator)

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

    async def atomic_create_role_managed_global_entities(
        self, creators: Sequence[RoleManagedGlobalEntityCreator[Any, TData]]
    ) -> list[TData]:
        """Insert several role-managed rows created in no scope atomically, preset
        roles included."""
        async with self._ops.write_ops() as w:
            return await w.atomic_create_role_managed_global_entities(creators)

    async def atomic_create_role_managed_entities(
        self, creators: Sequence[RoleManagedEntityCreator[Any, TData]]
    ) -> list[TData]:
        """Insert several role-managed entity rows atomically, each owned and governed
        by the scopes it is created in, preset roles included."""
        async with self._ops.write_ops() as w:
            return await w.atomic_create_role_managed_entities(creators)

    async def atomic_create_field_entities[TFieldData: FieldData](
        self, owner_id: Any, creators: Sequence[FieldCreator[Any, Any, TFieldData]]
    ) -> list[TFieldData]:
        """Insert several field rows sharing one owner, atomically."""
        async with self._ops.write_ops() as w:
            return await w.atomic_create_field_entities(owner_id, creators)

    async def create_dangling_field[TFieldData: FieldData](
        self, creator: DanglingFieldCreator[Any, TFieldData]
    ) -> TFieldData:
        async with self._ops.write_ops() as w:
            return await w.create_dangling_field(creator)

    async def atomic_create_fields[TOwnerID: EntityIdentifier, TFieldData: FieldData](
        self, creations: Sequence[FieldToCreate[TOwnerID, Any, TFieldData]]
    ) -> list[TFieldData]:
        """Insert field rows atomically, each under the owner named beside it."""
        async with self._ops.write_ops() as w:
            return await w.atomic_create_fields(creations)

    async def atomic_create_fields_with_nested[
        TOwnerID: EntityIdentifier,
        TFieldData: FieldData,
        TNestedData: FieldData,
    ](
        self,
        creations: Sequence[FieldToCreate[TOwnerID, Any, TFieldData]],
        nested_creators: Sequence[NestedFieldCreator[Any, Any, TNestedData]],
    ) -> list[TFieldData]:
        """Insert field rows and the rows each of them owns, in one transaction."""
        async with self._ops.write_ops() as w:
            return await w.atomic_create_fields_with_nested(creations, nested_creators)

    async def atomic_create_dangling_fields[TFieldData: FieldData](
        self, creators: Sequence[DanglingFieldCreator[Any, TFieldData]]
    ) -> list[TFieldData]:
        async with self._ops.write_ops() as w:
            return await w.atomic_create_dangling_fields(creators)

    async def atomic_create_dangling_fields_with_nested[
        TFieldData: FieldData,
        TNestedData: FieldData,
    ](
        self,
        creators: Sequence[DanglingFieldCreator[Any, TFieldData]],
        field_creators: Sequence[NestedFieldCreator[Any, Any, TNestedData]],
    ) -> list[TFieldData]:
        async with self._ops.write_ops() as w:
            return await w.atomic_create_dangling_fields_with_nested(creators, field_creators)

    async def purge_entity(self, purger: EntityPurger[Any, TData]) -> TData:
        """Hard-delete one entity row, tearing its scope down with it."""
        async with self._ops.write_ops() as w:
            data = await w.purge_entity(purger)
            if data is None:
                raise EntityNotFoundError(
                    f"{purger.row_class().__name__} {purger.entity_id()} not found"
                )
            return data

    async def purge_field_entity[TFieldData: FieldData](
        self, purger: FieldPurger[Any, TFieldData]
    ) -> TFieldData:
        """Hard-delete one field row; authorized through the owner, no membership work."""
        async with self._ops.write_ops() as w:
            data = await w.purge_field_entity(purger)
            if data is None:
                raise EntityNotFoundError(
                    f"{purger.row_class().__name__} {purger.target_id_value()} not found"
                )
            return data

    async def partial_bulk_purge_entities(
        self, purgers: Mapping[EntityIdentifier, EntityPurger[Any, TData]]
    ) -> BulkResultWithFailures[TData]:
        """Hard-delete each named entity independently, answering for every one."""
        async with self._ops.write_ops() as w:
            return await w.partial_bulk_purge_entities(purgers)

    async def partial_bulk_purge_field_entities[TFieldData: FieldData](
        self, purgers: Mapping[FieldIdentifier, FieldPurger[Any, TFieldData]]
    ) -> BulkFieldOpsResult[TFieldData]:
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

    async def upsert_field_entity[TFieldData: FieldData](
        self, owner_id: Any, upserter: FieldUpserter[Any, Any, TFieldData]
    ) -> TFieldData:
        """Insert or update a field row on conflict, under its owner. Never absent."""
        async with self._ops.write_ops() as w:
            return await w.upsert_field_entity(owner_id, upserter)

    async def update(self, updater: DataUpdater[Any, TData]) -> TData:
        async with self._ops.write_ops() as w:
            data = await w.update_data(updater)
            if data is None:
                raise EntityNotFoundError(
                    f"{updater.row_class.__name__} {updater.target_id_value()} not found"
                )
            return data

    async def update_guarded(self, updater: GuardedDataUpdater[Any, TData]) -> TData:
        """Apply a guarded update, telling a missing row from a refused one.

        The guard rides on the UPDATE, so the row it declined is read back in the same
        session rather than re-checked against a later state.
        """
        async with self._ops.write_ops() as w:
            data = await w.update_guarded_data(updater)
            if data is not None:
                return data
            row_name = f"{updater.row_class.__name__} {updater.target_id_value()}"
            if await w.row_exists(
                updater.row_class, updater.target_id_column(), updater.target_id_value()
            ):
                raise EntityWriteRefusedError(f"{row_name} refused the write")
            raise EntityNotFoundError(f"{row_name} not found")

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

    async def batch_purge_entities_in_scopes(
        self, scopes: Sequence[OperationScope], purger: EntityBatchPurger[Any, TData]
    ) -> list[TData]:
        """Delete every selected row within ``scopes``, which must not be empty."""
        async with self._ops.write_ops() as w:
            return await w.batch_purge_entities_in_scopes(scopes, purger)

    async def batch_purge_entities_in_global(
        self, purger: EntityBatchPurger[Any, TData]
    ) -> list[TData]:
        """Delete every selected row across the table; caller holds the authority."""
        async with self._ops.write_ops() as w:
            return await w.batch_purge_entities_in_global(purger)
