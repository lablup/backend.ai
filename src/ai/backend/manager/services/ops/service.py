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
    BulkCreateOpsAction,
    CreateOpsAction,
    GetOpsAction,
    LookupOpsAction,
    PurgeOpsAction,
    SearchOpsAction,
    UpdateOpsAction,
    UpsertOpsAction,
)
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntitiesOpsResult,
    EntityOpsResult,
    LookupOpsResult,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository

__all__ = (
    "GetService",
    "LookupService",
    "SearchService",
    "CreateService",
    "BulkCreateService",
    "BatchUpdateService",
    "BatchPurgeService",
    "UpdateService",
    "DeleteService",
    "UpsertService",
    "PurgeService",
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
    """Runs the action's searcher over the scopes it names."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: SearchOpsAction[Any, TData]) -> BatchOpsResult[TData]:
        result = await self._repository.search(action.to_searcher(), action.search_scopes())
        return BatchOpsResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )


class CreateService[TData: EntityData]:
    """Inserts the row the action's creator describes.

    Bounded by :class:`EntityData`, as the scope-shaped operations are: a create names a
    scope, so its result reports the id of what it produced rather than the action doing
    so, and the value that came back is the only thing that knows it.

    One entity, because ``create`` inserts one row. A bulk create is not wired through
    the generic path.
    """

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: CreateOpsAction[Any, TData]) -> CreatedEntityOpsResult[TData]:
        return CreatedEntityOpsResult(data=await self._repository.create(action.to_creator()))


class BulkCreateService[TData: EntityData]:
    """Inserts every row the action's creators describe, atomically."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: BulkCreateOpsAction[Any, TData]) -> EntitiesOpsResult[TData]:
        return EntitiesOpsResult(items=await self._repository.bulk_create(action.to_creators()))


class BatchUpdateService[TData: EntityData]:
    """Updates every row matching the action's spec, and names what it wrote."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: BatchUpdateOpsAction[Any, TData]) -> EntitiesOpsResult[TData]:
        return EntitiesOpsResult(
            items=await self._repository.batch_update(action.to_batch_updater())
        )


class BatchPurgeService[TData: EntityData]:
    """Hard-deletes every row the action's spec selects, and names what it removed."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: BatchPurgeOpsAction[Any, TData]) -> EntitiesOpsResult[TData]:
        return EntitiesOpsResult(items=await self._repository.batch_purge(action.to_batch_purger()))


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


class UpsertService[TData]:
    """Inserts or updates on conflict.

    The one service outside the standard six: ``upsert`` is not an
    ``ActionOperationType``, so it has no slot among create / update, but the write is
    distinct enough that folding it into either would misreport what ran.
    """

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: UpsertOpsAction[Any, TData]) -> EntityOpsResult[TData]:
        return EntityOpsResult(data=await self._repository.upsert(action.to_upserter()))


class PurgeService[TData]:
    """Hard-deletes the row the action's purger describes."""

    _repository: OpsRepository[TData]

    def __init__(self, repository: OpsRepository[TData]) -> None:
        self._repository = repository

    async def execute(self, action: PurgeOpsAction[Any, TData]) -> EntityOpsResult[TData]:
        return EntityOpsResult(data=await self._repository.purge(action.to_purger()))
