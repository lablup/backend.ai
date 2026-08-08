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
    BulkUpdateOpsAction,
    FieldEntityCreateOpsAction,
    FieldEntityPurgeOpsAction,
    GetOpsAction,
    GlobalBatchPurgeOpsAction,
    GlobalBatchUpdateOpsAction,
    GlobalEntityCreateOpsAction,
    GlobalEntityPurgeOpsAction,
    GlobalSearchOpsAction,
    LookupOpsAction,
    ScopedEntityBulkCreateOpsAction,
    ScopedEntityBulkPurgeOpsAction,
    ScopedEntityCreateOpsAction,
    ScopedEntityPurgeOpsAction,
    ScopedEntityUpsertOpsAction,
    SearchOpsAction,
    UpdateOpsAction,
)
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    BulkOpsResult,
    CreatedEntityOpsResult,
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
    "ScopedCreateService",
    "FieldCreateService",
    "FieldPurgeService",
    "ScopedBulkCreateService",
    "BulkUpdateService",
    "BulkDeleteService",
    "ScopedBulkPurgeService",
    "BatchUpdateService",
    "BatchPurgeService",
    "UpdateService",
    "DeleteService",
    "ScopedUpsertService",
    "GlobalPurgeService",
    "ScopedPurgeService",
)


class GetService[TData]:
    """Reads the entity the action's querier names."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: GetOpsAction[Any, TData]) -> EntityOpsResult[TData]:
        return EntityOpsResult(data=await self._repository.get(action.to_querier()))


class LookupService[TData: EntityData]:
    """Resolves the key the action's finder describes into an entity."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: LookupOpsAction[Any, TData]) -> LookupOpsResult[TData]:
        return LookupOpsResult(data=await self._repository.find(action.to_finder()))


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
    """Inserts the global-family row the action's creator describes."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: GlobalEntityCreateOpsAction[Any, TData]
    ) -> CreatedEntityOpsResult[TData]:
        return CreatedEntityOpsResult(
            data=await self._repository.create_global_entity(action.to_creator())
        )


class ScopedCreateService[TData: EntityData]:
    """Inserts the scoped-family row the action's creator describes; the write
    itself registers the row's declared membership."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: ScopedEntityCreateOpsAction[Any, TData]
    ) -> CreatedEntityOpsResult[TData]:
        return CreatedEntityOpsResult(
            data=await self._repository.create_scoped_entity(action.to_creator())
        )


class FieldCreateService[TData: EntityData]:
    """Inserts the field row the action's creator describes under the action's owner."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: FieldEntityCreateOpsAction[Any, Any, TData]
    ) -> CreatedEntityOpsResult[TData]:
        return CreatedEntityOpsResult(
            data=await self._repository.create_field_entity(action.to_creator(), action.owner_id())
        )


class FieldPurgeService[TData]:
    """Hard-deletes the field row the action's purger describes; no membership work."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: FieldEntityPurgeOpsAction[Any, TData]
    ) -> EntityOpsResult[TData]:
        return EntityOpsResult(data=await self._repository.purge_field_entity(action.to_purger()))


class ScopedBulkCreateService[TData: EntityData]:
    """Inserts every scoped row the action's creators describe, atomically."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: ScopedEntityBulkCreateOpsAction[Any, TData]
    ) -> EntitiesOpsResult[TData]:
        return EntitiesOpsResult(
            items=await self._repository.bulk_create_scoped_entities(action.to_creators())
        )


class BulkUpdateService[TData]:
    """Updates each entity the action named, answering for every one of them."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: BulkUpdateOpsAction[Any, TData]) -> BulkOpsResult[TData]:
        result = await self._repository.bulk_update(action.to_updaters())
        return BulkOpsResult(successes=result.successes, errors=result.errors)


class BulkDeleteService[TData]:
    """Soft-deletes each entity the action named.

    Takes ``BulkUpdateOpsAction`` for the same reason the single-entity delete does: the
    status transition is domain knowledge and ops has no delete operation to generalize.
    """

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: BulkUpdateOpsAction[Any, TData]) -> BulkOpsResult[TData]:
        result = await self._repository.bulk_update(action.to_updaters())
        return BulkOpsResult(successes=result.successes, errors=result.errors)


class ScopedBulkPurgeService[TData]:
    """Hard-deletes each scoped entity the action named, answering for every one."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: ScopedEntityBulkPurgeOpsAction[Any, TData]
    ) -> BulkOpsResult[TData]:
        result = await self._repository.bulk_purge_scoped_entities(action.to_purgers())
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


class ScopedUpsertService[TData]:
    """Inserts or updates a scoped entity on conflict, registering idempotently."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: ScopedEntityUpsertOpsAction[Any, TData]
    ) -> EntityOpsResult[TData]:
        return EntityOpsResult(
            data=await self._repository.upsert_scoped_entity(action.to_upserter())
        )


class GlobalPurgeService[TData]:
    """Hard-deletes the global-family row the action's purger describes."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: GlobalEntityPurgeOpsAction[Any, TData]
    ) -> EntityOpsResult[TData]:
        return EntityOpsResult(data=await self._repository.purge_global_entity(action.to_purger()))


class ScopedPurgeService[TData]:
    """Hard-deletes the scoped-family row, removing its membership with it."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(
        self, action: ScopedEntityPurgeOpsAction[Any, TData]
    ) -> EntityOpsResult[TData]:
        return EntityOpsResult(data=await self._repository.purge_scoped_entity(action.to_purger()))
