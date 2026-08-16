"""The standard six, once, for every domain whose service method only passes through.

An ops-backed action hands over its repository spec, the service passes it to the
repository, and the shared result carries the answer back — so a pass-through domain
writes neither a service method nor a repository method: it wires
:class:`~ai.backend.manager.repositories.ops.repository.OpsRepository` as it is. ``ActionOperationType`` and the
repository layer's standard six are already the same six words, so these line up with
both.

None of them take a hook or callback parameter. A domain that needs a branch is promoted
to a service method of its own, and that promotion has to be visible at the wiring site
rather than hidden in an argument.
"""

from typing import Any

from ai.backend.common.data.entity.types import EntityData
from ai.backend.manager.actions.v2.ops.base import (
    BatchPurgeOpsAction,
    BatchUpdateOpsAction,
    EntityAtomicCreateOpsAction,
    EntityCreateOpsAction,
    EntityPartialBulkPurgeOpsAction,
    EntityPurgeOpsAction,
    EntityUpsertOpsAction,
    FieldAtomicCreateOpsAction,
    FieldCreateOpsAction,
    FieldPartialBulkPurgeOpsAction,
    FieldPurgeOpsAction,
    FieldUpsertOpsAction,
    GetOpsAction,
    GlobalBatchPurgeOpsAction,
    GlobalBatchUpdateOpsAction,
    GlobalEntityAtomicCreateOpsAction,
    GlobalEntityCreateOpsAction,
    GlobalEntityPartialBulkPurgeOpsAction,
    GlobalEntityUpsertOpsAction,
    GlobalEntityWithFieldsCreateOpsAction,
    GlobalSearchOpsAction,
    LookupOpsAction,
    PartialBulkUpdateOpsAction,
    RoleManagedEntityAtomicCreateOpsAction,
    RoleManagedEntityCreateOpsAction,
    SearchOpsAction,
    UpdateOpsAction,
)
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    BulkOpsResult,
    CreatedEntityOpsResult,
    CreatedEntityWithFieldsOpsResult,
    EntitiesOpsResult,
    EntityOpsResult,
    LookupOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository

__all__ = (
    "GetService",
    "LookupService",
    "SearchService",
    "GlobalSearchService",
    "GlobalCreateService",
    "GlobalCreateWithFieldsService",
    "EntityCreateService",
    "RoleManagedEntityCreateService",
    "FieldCreateService",
    "GlobalAtomicCreateService",
    "EntityAtomicCreateService",
    "RoleManagedEntityAtomicCreateService",
    "FieldAtomicCreateService",
    "GlobalPurgeService",
    "EntityPurgeService",
    "FieldPurgeService",
    "GlobalPartialBulkPurgeService",
    "EntityPartialBulkPurgeService",
    "FieldPartialBulkPurgeService",
    "GlobalUpsertService",
    "EntityUpsertService",
    "FieldUpsertService",
    "UpdateService",
    "DeleteService",
    "RestoreService",
    "PartialBulkUpdateService",
    "PartialBulkDeleteService",
    "PartialBulkRestoreService",
    "BatchUpdateService",
    "GlobalBatchUpdateService",
    "BatchPurgeService",
    "GlobalBatchPurgeService",
)


class GetService[TData]:
    """Reads the entity the action's querier names."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: GetOpsAction[Any, TData]) -> EntityOpsResult[TData]:
        return EntityOpsResult(data=await self._repository.get(action.to_querier()))


class LookupService[TData: EntityData]:
    """Resolves the key the action's lookup spec describes into an entity."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: LookupOpsAction[Any, TData]) -> LookupOpsResult[TData]:
        return LookupOpsResult(data=await self._repository.lookup(action.to_lookup()))


class SearchService[TData: EntityData]:
    """Runs the action's searcher over the scopes it names.

    Raises rather than widening if the action names none: see
    ``SearchOpsAction.operation_scopes``. An unscoped read is
    :class:`GlobalSearchService`, wired from a different action shape.
    """

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: SearchOpsAction[Any, TData]) -> ScopedBatchOpsResult[TData]:
        result = await self._repository.search_in_scopes(
            action.operation_scopes(), action.to_searcher()
        )
        return ScopedBatchOpsResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )


class GlobalSearchService[TData]:
    """Runs the action's searcher across the entire table.

    Wired from ``BaseGlobalAction``, whose SUPERADMIN gate is what answers for an
    unscoped scan. Needs no :class:`EntityData`: the global shape asks its result to
    name nothing.
    """

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: GlobalSearchOpsAction[Any, TData]) -> BatchOpsResult[TData]:
        result = await self._repository.search_in_global(action.to_searcher())
        return BatchOpsResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )


class GlobalCreateService[TData: EntityData]:
    """Inserts the global row the action's creator describes."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: GlobalEntityCreateOpsAction[Any, TData]
    ) -> CreatedEntityOpsResult[TData]:
        return CreatedEntityOpsResult(
            data=await self._repository.create_global_entity(action.to_creator())
        )


class GlobalCreateWithFieldsService[TData: EntityData]:
    """Inserts a global row and the field rows it owns, in one transaction."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: GlobalEntityWithFieldsCreateOpsAction[Any, TData, Any, Any]
    ) -> CreatedEntityWithFieldsOpsResult[TData, Any]:
        result = await self._repository.create_global_entity_with_fields(
            action.to_creator(), action.to_field_creators()
        )
        return CreatedEntityWithFieldsOpsResult(data=result.data, fields=result.fields)


class EntityCreateService[TData: EntityData]:
    """Inserts the entity row the action's creator describes; the write provisions
    the row's scope and memberships with it."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: EntityCreateOpsAction[Any, TData]
    ) -> CreatedEntityOpsResult[TData]:
        return CreatedEntityOpsResult(
            data=await self._repository.create_entity(action.to_creator())
        )


class RoleManagedEntityCreateService[TData: EntityData]:
    """Inserts the role-managed entity row, preset roles included."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: RoleManagedEntityCreateOpsAction[Any, TData]
    ) -> CreatedEntityOpsResult[TData]:
        return CreatedEntityOpsResult(
            data=await self._repository.create_role_managed_entity(action.to_creator())
        )


class FieldCreateService[TData: EntityData]:
    """Inserts the field row the action's creator describes under the action's owner."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: FieldCreateOpsAction[Any, Any, TData]
    ) -> CreatedEntityOpsResult[TData]:
        return CreatedEntityOpsResult(
            data=await self._repository.create_field_entity(action.owner_id(), action.to_creator())
        )


class GlobalAtomicCreateService[TData: EntityData]:
    """Inserts every global row the action's creators describe, atomically."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: GlobalEntityAtomicCreateOpsAction[Any, TData]
    ) -> EntitiesOpsResult[TData]:
        return EntitiesOpsResult(
            items=await self._repository.atomic_create_global_entities(action.to_creators())
        )


class EntityAtomicCreateService[TData: EntityData]:
    """Inserts every entity row the action's creators describe, atomically."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: EntityAtomicCreateOpsAction[Any, TData]
    ) -> EntitiesOpsResult[TData]:
        return EntitiesOpsResult(
            items=await self._repository.atomic_create_entities(action.to_creators())
        )


class RoleManagedEntityAtomicCreateService[TData: EntityData]:
    """Inserts every role-managed entity row atomically, preset roles included."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: RoleManagedEntityAtomicCreateOpsAction[Any, TData]
    ) -> EntitiesOpsResult[TData]:
        return EntitiesOpsResult(
            items=await self._repository.atomic_create_role_managed_entities(action.to_creators())
        )


class FieldAtomicCreateService[TData: EntityData]:
    """Inserts every field row the action's creators describe under the action's owner."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: FieldAtomicCreateOpsAction[Any, Any, TData]
    ) -> EntitiesOpsResult[TData]:
        return EntitiesOpsResult(
            items=await self._repository.atomic_create_field_entities(
                action.owner_id(), action.to_creators()
            )
        )


class GlobalPurgeService[TData]:
    """Hard-deletes the global row the action's purger describes."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: EntityPurgeOpsAction[Any, TData]) -> EntityOpsResult[TData]:
        return EntityOpsResult(data=await self._repository.purge_entity(action.to_purger()))


class EntityPurgeService[TData]:
    """Hard-deletes the entity row, tearing its scope down with it."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: EntityPurgeOpsAction[Any, TData]) -> EntityOpsResult[TData]:
        return EntityOpsResult(data=await self._repository.purge_entity(action.to_purger()))


class FieldPurgeService[TData]:
    """Hard-deletes the field row the action's purger describes; no membership work."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: FieldPurgeOpsAction[Any, TData]) -> EntityOpsResult[TData]:
        return EntityOpsResult(data=await self._repository.purge_field_entity(action.to_purger()))


class GlobalPartialBulkPurgeService[TData]:
    """Hard-deletes each global entity the action named, answering for every one."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: GlobalEntityPartialBulkPurgeOpsAction[Any, TData]
    ) -> BulkOpsResult[TData]:
        result = await self._repository.partial_bulk_purge_entities(action.to_purgers())
        return BulkOpsResult(successes=result.successes, errors=result.errors)


class EntityPartialBulkPurgeService[TData]:
    """Hard-deletes each entity the action named, answering for every one."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: EntityPartialBulkPurgeOpsAction[Any, TData]
    ) -> BulkOpsResult[TData]:
        result = await self._repository.partial_bulk_purge_entities(action.to_purgers())
        return BulkOpsResult(successes=result.successes, errors=result.errors)


class FieldPartialBulkPurgeService[TData]:
    """Hard-deletes each field row the action named, answering for every one."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: FieldPartialBulkPurgeOpsAction[Any, TData]
    ) -> BulkOpsResult[TData]:
        result = await self._repository.partial_bulk_purge_field_entities(action.to_purgers())
        return BulkOpsResult(successes=result.successes, errors=result.errors)


class GlobalUpsertService[TData]:
    """Inserts or updates a global row on conflict; nothing is registered."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: GlobalEntityUpsertOpsAction[Any, TData]
    ) -> EntityOpsResult[TData]:
        return EntityOpsResult(
            data=await self._repository.upsert_global_entity(action.to_upserter())
        )


class EntityUpsertService[TData]:
    """Inserts or updates an entity row on conflict; the scope stays provisioned
    idempotently."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: EntityUpsertOpsAction[Any, TData]) -> EntityOpsResult[TData]:
        return EntityOpsResult(data=await self._repository.upsert_entity(action.to_upserter()))


class FieldUpsertService[TData]:
    """Inserts or updates a field row on conflict, under the action's owner."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: FieldUpsertOpsAction[Any, Any, TData]
    ) -> EntityOpsResult[TData]:
        return EntityOpsResult(
            data=await self._repository.upsert_field_entity(action.owner_id(), action.to_upserter())
        )


class UpdateService[TData]:
    """Applies the action's updater."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: UpdateOpsAction[Any, TData]) -> EntityOpsResult[TData]:
        return EntityOpsResult(data=await self._repository.update(action.to_updater()))


class DeleteService[TData]:
    """Soft-deletes by applying the action's updater.

    Takes ``UpdateOpsAction`` rather than a delete-shaped base because a soft delete is
    a status transition: which column moves to which value is domain knowledge, and
    ``DBOpsProvider`` has no delete operation to generalize. The action still declares
    ``operation_type() == DELETE``, so RBAC and the audit trail see a delete; only the
    write underneath is an update.
    """

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: UpdateOpsAction[Any, TData]) -> EntityOpsResult[TData]:
        return EntityOpsResult(data=await self._repository.update(action.to_updater()))


class RestoreService[TData]:
    """Restores by applying the action's updater.

    Identical to :class:`DeleteService` under the hood. The action declares
    ``operation_type() == RESTORE``, so the audit says restore while the permission
    checked stays soft-delete.
    """

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: UpdateOpsAction[Any, TData]) -> EntityOpsResult[TData]:
        return EntityOpsResult(data=await self._repository.update(action.to_updater()))


class PartialBulkUpdateService[TData]:
    """Updates each entity the action named, answering for every one of them."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: PartialBulkUpdateOpsAction[Any, TData]) -> BulkOpsResult[TData]:
        result = await self._repository.partial_bulk_update(action.to_updaters())
        return BulkOpsResult(successes=result.successes, errors=result.errors)


class PartialBulkDeleteService[TData]:
    """Soft-deletes each entity the action named.

    Takes ``PartialBulkUpdateOpsAction`` for the same reason the single-entity delete does: the
    status transition is domain knowledge and ops has no delete operation to generalize.
    """

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: PartialBulkUpdateOpsAction[Any, TData]) -> BulkOpsResult[TData]:
        result = await self._repository.partial_bulk_update(action.to_updaters())
        return BulkOpsResult(successes=result.successes, errors=result.errors)


class PartialBulkRestoreService[TData]:
    """Restores each entity the action named, answering for every one of them."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: PartialBulkUpdateOpsAction[Any, TData]) -> BulkOpsResult[TData]:
        result = await self._repository.partial_bulk_update(action.to_updaters())
        return BulkOpsResult(successes=result.successes, errors=result.errors)


class BatchUpdateService[TData: EntityData]:
    """Updates every matching row within the scopes the action names."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: BatchUpdateOpsAction[Any, TData]) -> EntitiesOpsResult[TData]:
        return EntitiesOpsResult(
            items=await self._repository.batch_update_in_scopes(
                action.operation_scopes(), action.to_batch_updater()
            )
        )


class GlobalBatchUpdateService[TData: EntityData]:
    """Updates every matching row across the table; the SUPERADMIN gate answers."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: GlobalBatchUpdateOpsAction[Any, TData]
    ) -> EntitiesOpsResult[TData]:
        return EntitiesOpsResult(
            items=await self._repository.batch_update_in_global(action.to_batch_updater())
        )


class BatchPurgeService[TData: EntityData]:
    """Hard-deletes every selected row within the scopes the action names."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: BatchPurgeOpsAction[Any, TData]) -> EntitiesOpsResult[TData]:
        return EntitiesOpsResult(
            items=await self._repository.batch_purge_in_scopes(
                action.operation_scopes(), action.to_batch_purger()
            )
        )


class GlobalBatchPurgeService[TData: EntityData]:
    """Hard-deletes every selected row across the table; the SUPERADMIN gate answers."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: GlobalBatchPurgeOpsAction[Any, TData]
    ) -> EntitiesOpsResult[TData]:
        return EntitiesOpsResult(
            items=await self._repository.batch_purge_in_global(action.to_batch_purger())
        )
