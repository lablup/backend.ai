"""Holds what every processor is built from, so a domain names no monitor or validator.

A service-backed operation is wrapped by its target shape — ``single_entity``,
``scope``, ``bulk``, ``global_scope``, ``lookup`` — and there is no factory per
operation, because the shape is all that changes: the operation is on the action,
where the audit trail and the RBAC validators read it from. An ``<shape>_<operation>_ops``
factory does vary by operation, which decides the generic service it builds, the spec it
demands of the action, and the result type.

Every factory takes the action class it wires as its first argument: the processor is
typed by that class, and the registry accumulates every wired spec — the catalog of
entity-operation combinations actually in use.

The ``validators`` / ``monitors`` arguments only append — what the shape carries is
always applied.
"""

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Any

from ai.backend.common.data.entity.types import EntityData
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.types import ActionSpec
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.bulk.monitor import BulkActionMonitor
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.bulk.result import BaseBulkActionResult
from ai.backend.manager.actions.v2.bulk.validator import BulkActionValidator
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.monitor import GlobalActionMonitor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.global_scope.validator import GlobalActionValidator
from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction, BaseLookupActionResult
from ai.backend.manager.actions.v2.lookup.monitor import LookupActionMonitor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.lookup.validator import LookupActionValidator
from ai.backend.manager.actions.v2.ops.base import (
    BatchPurgeGlobalOpsAction,
    BatchPurgeScopeOpsAction,
    BatchUpdateGlobalOpsAction,
    BatchUpdateScopeOpsAction,
    BulkCreateEntityOpsAction,
    BulkCreateFieldEntityOpsAction,
    BulkCreateGlobalEntityOpsAction,
    BulkCreateRoleManagedEntityOpsAction,
    BulkPurgeEntityOpsAction,
    BulkPurgeFieldEntityOpsAction,
    BulkPurgeGlobalEntityOpsAction,
    CreateEntityOpsAction,
    CreateFieldEntityOpsAction,
    CreateGlobalOpsAction,
    CreateRoleManagedEntityOpsAction,
    DeleteBulkOpsAction,
    DeleteSingleEntityOpsAction,
    GetSingleEntityOpsAction,
    LookupEntityOpsAction,
    OperationScopeOpsAction,
    PurgeEntityOpsAction,
    PurgeFieldEntityOpsAction,
    PurgeGlobalOpsAction,
    SearchGlobalOpsAction,
    UpdateBulkOpsAction,
    UpdateGlobalOpsAction,
    UpdateSingleEntityOpsAction,
    UpsertEntityOpsAction,
    UpsertFieldEntityOpsAction,
    UpsertGlobalOpsAction,
    UpsertRoleManagedEntityOpsAction,
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
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.monitor import ScopeActionMonitor
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.actions.v2.scope.validator import ScopeActionValidator
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.v2.single_entity.monitor import SingleEntityActionMonitor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.actions.v2.single_entity.validator import SingleEntityActionValidator
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.ops.service import (
    BatchPurgeService,
    BatchUpdateService,
    BulkDeleteService,
    BulkUpdateService,
    DeleteService,
    EntityBulkCreateService,
    EntityBulkPurgeService,
    EntityCreateService,
    EntityPurgeService,
    EntityUpsertService,
    FieldBulkCreateService,
    FieldBulkPurgeService,
    FieldCreateService,
    FieldPurgeService,
    FieldUpsertService,
    GetService,
    GlobalBatchPurgeService,
    GlobalBatchUpdateService,
    GlobalBulkCreateService,
    GlobalBulkPurgeService,
    GlobalCreateService,
    GlobalPurgeService,
    GlobalSearchService,
    GlobalUpsertService,
    LookupService,
    RoleManagedEntityBulkCreateService,
    RoleManagedEntityCreateService,
    RoleManagedEntityUpsertService,
    SearchService,
    UpdateService,
)

__all__ = (
    "ProcessorDependencies",
    "ProcessorGroup",
    "ProcessorRegistry",
)


@dataclass(frozen=True)
class ProcessorDependencies[TData: EntityData]:
    monitors: ActionMonitors
    validators: ActionValidators
    repository: OpsRepository[TData]


class ProcessorGroup[TData: EntityData]:
    _deps: ProcessorDependencies[TData]
    _specs: list[ActionSpec]

    def __init__(self, deps: ProcessorDependencies[TData], specs: list[ActionSpec]) -> None:
        self._deps = deps
        self._specs = specs

    def _record(self, spec: ActionSpec) -> None:
        self._specs.append(spec)

    def single_entity[TAction: BaseSingleEntityAction, TResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, TResult]:
        self._record(action_cls.spec())
        return SingleEntityActionProcessor(
            func,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def scope[TAction: BaseScopeAction, TResult: BaseScopeActionResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, TResult]:
        self._record(action_cls.spec())
        return ScopeActionProcessor(
            func,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(*self._deps.validators.scope, *validators),
        )

    def bulk[TAction: BaseBulkAction, TResult: BaseBulkActionResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[BulkActionValidator] = (),
        monitors: Sequence[BulkActionMonitor] = (),
    ) -> BulkActionProcessor[TAction, TResult]:
        self._record(action_cls.spec())
        return BulkActionProcessor(
            func,
            monitors=(*self._deps.monitors.bulk, *monitors),
            validators=(*self._deps.validators.bulk, *validators),
        )

    def global_scope[TAction: BaseGlobalAction, TResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, TResult]:
        self._record(action_cls.spec())
        return GlobalActionProcessor(
            func,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )

    def lookup[TAction: BaseLookupAction, TResult: BaseLookupActionResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[LookupActionValidator] = (),
        monitors: Sequence[LookupActionMonitor] = (),
    ) -> LookupActionProcessor[TAction, TResult]:
        self._record(action_cls.spec())
        return LookupActionProcessor(
            func,
            monitors=(*self._deps.monitors.lookup, *monitors),
            validators=(*self._deps.validators.lookup, *validators),
        )

    def lookup_ops[TAction: LookupEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[LookupActionValidator] = (),
        monitors: Sequence[LookupActionMonitor] = (),
    ) -> LookupActionProcessor[TAction, LookupOpsResult[TData]]:
        self._record(action_cls.spec())
        return LookupActionProcessor(
            LookupService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.lookup, *monitors),
            validators=(*self._deps.validators.lookup, *validators),
        )

    def single_get_ops[TAction: GetSingleEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, EntityOpsResult[TData]]:
        self._record(action_cls.spec())
        return SingleEntityActionProcessor(
            GetService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def scope_search_ops[TAction: OperationScopeOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, ScopedBatchOpsResult[TData]]:
        self._record(action_cls.spec())
        return ScopeActionProcessor(
            SearchService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(*self._deps.validators.scope, *validators),
        )

    def global_search_ops[TAction: SearchGlobalOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, BatchOpsResult[TData]]:
        self._record(action_cls.spec())
        return GlobalActionProcessor(
            GlobalSearchService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )

    def global_create_ops[TAction: CreateGlobalOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, CreatedEntityOpsResult[TData]]:
        self._record(action_cls.spec())
        return GlobalActionProcessor(
            GlobalCreateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )

    def entity_create_ops[TAction: CreateEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, CreatedEntityOpsResult[TData]]:
        self._record(action_cls.spec())
        return ScopeActionProcessor(
            EntityCreateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(*self._deps.validators.scope, *validators),
        )

    def role_managed_create_ops[TAction: CreateRoleManagedEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, CreatedEntityOpsResult[TData]]:
        self._record(action_cls.spec())
        return ScopeActionProcessor(
            RoleManagedEntityCreateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(*self._deps.validators.scope, *validators),
        )

    def field_create_ops[TAction: CreateFieldEntityOpsAction[Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, CreatedEntityOpsResult[TData]]:
        self._record(action_cls.spec())
        return SingleEntityActionProcessor(
            FieldCreateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def global_bulk_create_ops[TAction: BulkCreateGlobalEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, EntitiesOpsResult[TData]]:
        self._record(action_cls.spec())
        return GlobalActionProcessor(
            GlobalBulkCreateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )

    def entity_bulk_create_ops[TAction: BulkCreateEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, EntitiesOpsResult[TData]]:
        self._record(action_cls.spec())
        return ScopeActionProcessor(
            EntityBulkCreateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(*self._deps.validators.scope, *validators),
        )

    def role_managed_bulk_create_ops[TAction: BulkCreateRoleManagedEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, EntitiesOpsResult[TData]]:
        self._record(action_cls.spec())
        return ScopeActionProcessor(
            RoleManagedEntityBulkCreateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(*self._deps.validators.scope, *validators),
        )

    def field_bulk_create_ops[TAction: BulkCreateFieldEntityOpsAction[Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, EntitiesOpsResult[TData]]:
        self._record(action_cls.spec())
        return SingleEntityActionProcessor(
            FieldBulkCreateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def global_purge_ops[TAction: PurgeGlobalOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, EntityOpsResult[TData]]:
        self._record(action_cls.spec())
        return GlobalActionProcessor(
            GlobalPurgeService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )

    def entity_purge_ops[TAction: PurgeEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, EntityOpsResult[TData]]:
        self._record(action_cls.spec())
        return SingleEntityActionProcessor(
            EntityPurgeService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def field_purge_ops[TAction: PurgeFieldEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, EntityOpsResult[TData]]:
        self._record(action_cls.spec())
        return SingleEntityActionProcessor(
            FieldPurgeService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def global_bulk_purge_ops[TAction: BulkPurgeGlobalEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[BulkActionValidator] = (),
        monitors: Sequence[BulkActionMonitor] = (),
    ) -> BulkActionProcessor[TAction, BulkOpsResult[TData]]:
        self._record(action_cls.spec())
        return BulkActionProcessor(
            GlobalBulkPurgeService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.bulk, *monitors),
            validators=(*self._deps.validators.bulk, *validators),
        )

    def entity_bulk_purge_ops[TAction: BulkPurgeEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[BulkActionValidator] = (),
        monitors: Sequence[BulkActionMonitor] = (),
    ) -> BulkActionProcessor[TAction, BulkOpsResult[TData]]:
        self._record(action_cls.spec())
        return BulkActionProcessor(
            EntityBulkPurgeService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.bulk, *monitors),
            validators=(*self._deps.validators.bulk, *validators),
        )

    def field_bulk_purge_ops[TAction: BulkPurgeFieldEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[BulkActionValidator] = (),
        monitors: Sequence[BulkActionMonitor] = (),
    ) -> BulkActionProcessor[TAction, BulkOpsResult[TData]]:
        self._record(action_cls.spec())
        return BulkActionProcessor(
            FieldBulkPurgeService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.bulk, *monitors),
            validators=(*self._deps.validators.bulk, *validators),
        )

    def global_upsert_ops[TAction: UpsertGlobalOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, EntityOpsResult[TData]]:
        self._record(action_cls.spec())
        return GlobalActionProcessor(
            GlobalUpsertService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )

    def entity_upsert_ops[TAction: UpsertEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, EntityOpsResult[TData]]:
        self._record(action_cls.spec())
        return SingleEntityActionProcessor(
            EntityUpsertService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def role_managed_upsert_ops[TAction: UpsertRoleManagedEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, EntityOpsResult[TData]]:
        self._record(action_cls.spec())
        return SingleEntityActionProcessor(
            RoleManagedEntityUpsertService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def field_upsert_ops[TAction: UpsertFieldEntityOpsAction[Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, EntityOpsResult[TData]]:
        self._record(action_cls.spec())
        return SingleEntityActionProcessor(
            FieldUpsertService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def global_update_ops[TAction: UpdateGlobalOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, EntityOpsResult[TData]]:
        self._record(action_cls.spec())
        return GlobalActionProcessor(
            UpdateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )

    def single_update_ops[TAction: UpdateSingleEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, EntityOpsResult[TData]]:
        self._record(action_cls.spec())
        return SingleEntityActionProcessor(
            UpdateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def single_delete_ops[TAction: DeleteSingleEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, EntityOpsResult[TData]]:
        self._record(action_cls.spec())
        return SingleEntityActionProcessor(
            DeleteService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def bulk_update_ops[TAction: UpdateBulkOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[BulkActionValidator] = (),
        monitors: Sequence[BulkActionMonitor] = (),
    ) -> BulkActionProcessor[TAction, BulkOpsResult[TData]]:
        self._record(action_cls.spec())
        return BulkActionProcessor(
            BulkUpdateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.bulk, *monitors),
            validators=(*self._deps.validators.bulk, *validators),
        )

    def bulk_delete_ops[TAction: DeleteBulkOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[BulkActionValidator] = (),
        monitors: Sequence[BulkActionMonitor] = (),
    ) -> BulkActionProcessor[TAction, BulkOpsResult[TData]]:
        self._record(action_cls.spec())
        return BulkActionProcessor(
            BulkDeleteService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.bulk, *monitors),
            validators=(*self._deps.validators.bulk, *validators),
        )

    def scope_batch_update_ops[TAction: BatchUpdateScopeOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, EntitiesOpsResult[TData]]:
        self._record(action_cls.spec())
        return ScopeActionProcessor(
            BatchUpdateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(*self._deps.validators.scope, *validators),
        )

    def global_batch_update_ops[TAction: BatchUpdateGlobalOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, EntitiesOpsResult[TData]]:
        self._record(action_cls.spec())
        return GlobalActionProcessor(
            GlobalBatchUpdateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )

    def scope_batch_purge_ops[TAction: BatchPurgeScopeOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, EntitiesOpsResult[TData]]:
        self._record(action_cls.spec())
        return ScopeActionProcessor(
            BatchPurgeService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(*self._deps.validators.scope, *validators),
        )

    def global_batch_purge_ops[TAction: BatchPurgeGlobalOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, EntitiesOpsResult[TData]]:
        self._record(action_cls.spec())
        return GlobalActionProcessor(
            GlobalBatchPurgeService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )


class ProcessorRegistry[TData: EntityData]:
    _deps: ProcessorDependencies[TData]
    _specs: list[ActionSpec]

    def __init__(self, deps: ProcessorDependencies[TData]) -> None:
        self._deps = deps
        self._specs = []

    def group(self) -> ProcessorGroup[TData]:
        return ProcessorGroup(self._deps, self._specs)

    def wired_specs(self) -> Sequence[ActionSpec]:
        """Every spec wired through this registry's groups, in wiring order."""
        return tuple(self._specs)
