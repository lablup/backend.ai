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

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Any

from ai.backend.common.data.entity.types import EntityData, FieldData
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.bulk.monitor import BulkActionMonitor
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.bulk.result import BaseBulkActionResult
from ai.backend.manager.actions.v2.bulk.validator import BulkActionValidator
from ai.backend.manager.actions.v2.field.base import BaseSingleFieldAction
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.bulk_processor import (
    BulkFieldActionProcessor,
    OwnerBulkLookupProcessor,
)
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.ops import (
    DeleteFieldOpsAction,
    GetFieldOpsAction,
    PartialBulkPurgeFieldOpsAction,
    PurgeFieldOpsAction,
    RestoreFieldOpsAction,
    UpdateFieldOpsAction,
)
from ai.backend.manager.actions.v2.field.processor import (
    OwnerLookupProcessor,
    SingleFieldActionProcessor,
)
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.monitor import GlobalActionMonitor
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.global_scope.validator import GlobalActionValidator
from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction, BaseLookupActionResult
from ai.backend.manager.actions.v2.lookup.bulk_processor import BulkLookupActionProcessor
from ai.backend.manager.actions.v2.lookup.monitor import LookupActionMonitor
from ai.backend.manager.actions.v2.lookup.processor import (
    LookupActionProcessor,
)
from ai.backend.manager.actions.v2.lookup.validator import LookupActionValidator
from ai.backend.manager.actions.v2.ops.base import (
    AtomicCreateEntityOpsAction,
    AtomicCreateFieldOpsAction,
    AtomicCreateGlobalEntityOpsAction,
    AtomicCreateRoleManagedEntityOpsAction,
    AtomicUpsertEntityOpsAction,
    BatchPurgeGlobalOpsAction,
    BatchPurgeScopeOpsAction,
    BatchUpdateGlobalOpsAction,
    BatchUpdateScopeOpsAction,
    CreateEntityOpsAction,
    CreateFieldOpsAction,
    CreateGlobalOpsAction,
    CreateGlobalWithFieldsOpsAction,
    CreateRoleManagedEntityOpsAction,
    DeletePartialBulkOpsAction,
    DeleteSingleEntityOpsAction,
    GetGlobalOpsAction,
    GetSingleEntityOpsAction,
    LookupEntityOpsAction,
    OperationScopeOpsAction,
    PartialBulkPurgeEntityOpsAction,
    PartialBulkPurgeGlobalEntityOpsAction,
    PurgeEntityOpsAction,
    RestorePartialBulkOpsAction,
    RestoreSingleEntityOpsAction,
    SearchGlobalOpsAction,
    UpdateGlobalOpsAction,
    UpdatePartialBulkOpsAction,
    UpdateSingleEntityOpsAction,
    UpsertEntityOpsAction,
    UpsertFieldOpsAction,
    UpsertGlobalOpsAction,
)
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    BulkOpsResult,
    CreatedEntityOpsResult,
    CreatedEntityWithFieldsOpsResult,
    CreatedFieldOpsResult,
    EntitiesOpsResult,
    EntityOpsResult,
    FieldsOpsResult,
    LookupOpsResult,
    ScopedBatchOpsResult,
    ScopedFieldsOpsResult,
)
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.monitor import ScopeActionMonitor
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.actions.v2.scope.validator import ScopeActionValidator
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.v2.single_entity.monitor import SingleEntityActionMonitor
from ai.backend.manager.actions.v2.single_entity.processor import (
    PublicSingleEntityActionProcessor,
    SingleEntityActionProcessor,
)
from ai.backend.manager.actions.v2.single_entity.validator import SingleEntityActionValidator
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.errors.common import ServerMisconfiguredError
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.ops.service import (
    BatchPurgeService,
    BatchUpdateService,
    BulkFieldOwnerLookupService,
    DeleteService,
    EntityAtomicCreateService,
    EntityAtomicUpsertService,
    EntityCreateService,
    EntityPartialBulkPurgeService,
    EntityPurgeService,
    EntityUpsertService,
    FieldAtomicCreateService,
    FieldCreateService,
    FieldOwnerLookupService,
    FieldPartialBulkPurgeService,
    FieldPurgeService,
    FieldUpsertService,
    GetService,
    GlobalAtomicCreateService,
    GlobalBatchPurgeService,
    GlobalBatchUpdateService,
    GlobalCreateService,
    GlobalCreateWithFieldsService,
    GlobalPartialBulkPurgeService,
    GlobalSearchService,
    GlobalUpsertService,
    LookupService,
    PartialBulkDeleteService,
    PartialBulkRestoreService,
    PartialBulkUpdateService,
    RestoreService,
    RoleManagedEntityAtomicCreateService,
    RoleManagedEntityCreateService,
    SearchFieldsService,
    SearchService,
    UpdateService,
)

__all__ = (
    "ProcessorDependencies",
    "ProcessorGroup",
    "FieldProcessorGroup",
    "ProcessorRegistry",
)


@dataclass(frozen=True)
class ProcessorDependencies[TData: EntityData]:
    monitors: ActionMonitors
    validators: ActionValidators
    repository: OpsRepository[TData]


class ProcessorGroup[TData: EntityData]:
    _deps: ProcessorDependencies[TData]
    _actions: list[type[Any]]

    def __init__(self, deps: ProcessorDependencies[TData], actions: list[type[Any]]) -> None:
        self._deps = deps
        self._actions = actions

    @property
    def deps(self) -> ProcessorDependencies[TData]:
        """Read by :class:`FieldProcessorGroup`, which builds processors of this group."""
        return self._deps

    def record(self, action_cls: type[Any]) -> None:
        """Record a class wired through a sub-group, so one catalog holds them all."""
        self._record(action_cls)

    def _record(self, action_cls: type[Any]) -> None:
        """Keep the class itself: every classmethod it declares — the operation, the
        action name, the id class — is then readable from one catalog."""
        self._actions.append(action_cls)

    def single_entity[TAction: BaseSingleEntityAction, TResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, TResult]:
        self._record(action_cls)
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
        self._record(action_cls)
        return ScopeActionProcessor(
            func,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(*self._deps.validators.scope, *validators),
        )

    def anonymous_scope[TAction: BaseScopeAction, TResult: BaseScopeActionResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, TResult]:
        """A scope read that runs before anyone has signed in.

        No gate at all, not even authentication -- ``public`` in this layer means every
        authenticated caller, which is still one step narrower. What keeps it safe is
        the read itself: naming no principal is what limits it to what is published.

        Reads only, checked here: a write must never reach an ungated path.
        """
        operation_type = action_cls.operation_type()
        if operation_type not in ActionOperationType.read_operations():
            raise ServerMisconfiguredError(
                f"{action_cls.__name__} declares operation_type()={operation_type}, "
                "but the anonymous path only accepts read actions."
            )
        self._record(action_cls)
        return ScopeActionProcessor(
            func,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(),
        )

    def bulk[TAction: BaseBulkAction, TResult: BaseBulkActionResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[BulkActionValidator] = (),
        monitors: Sequence[BulkActionMonitor] = (),
    ) -> BulkActionProcessor[TAction, TResult]:
        self._record(action_cls)
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
        self._record(action_cls)
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
        self._record(action_cls)
        return LookupActionProcessor(
            func,
            monitors=(*self._deps.monitors.lookup, *monitors),
            validators=(*self._deps.validators.lookup, *validators),
            post_validators=self._deps.validators.single_entity,
        )

    def lookup_ops[TAction: LookupEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[LookupActionValidator] = (),
        monitors: Sequence[LookupActionMonitor] = (),
    ) -> LookupActionProcessor[TAction, LookupOpsResult[TData]]:
        self._record(action_cls)
        return LookupActionProcessor(
            LookupService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.lookup, *monitors),
            validators=(*self._deps.validators.lookup, *validators),
            post_validators=self._deps.validators.single_entity,
        )

    def public_lookup_ops[TAction: LookupEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[LookupActionValidator] = (),
        monitors: Sequence[LookupActionMonitor] = (),
    ) -> LookupActionProcessor[TAction, LookupOpsResult[TData]]:
        """A key every authenticated caller may resolve: no post-validators, so the
        resolved entity carries no permission."""
        self._record(action_cls)
        return LookupActionProcessor(
            LookupService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.lookup, *monitors),
            validators=(*self._deps.validators.lookup, *validators),
        )

    def field_group[TFieldData: FieldData](
        self,
        data_cls: type[TFieldData],
        owner_lookup_action_cls: type[LookupFieldOwnerOpsAction[Any, Any]],
        bulk_owner_lookup_action_cls: type[LookupBulkFieldOwnerOpsAction[Any, Any]],
    ) -> FieldProcessorGroup[TFieldData]:
        """The operations over one kind of field row.

        Builds the owner lookups itself: they are not operations a domain wires, only
        the step every field operation runs first — one row at a time or many.
        """
        self._record(owner_lookup_action_cls)
        self._record(bulk_owner_lookup_action_cls)
        owner_lookup: OwnerLookupProcessor = LookupActionProcessor(
            FieldOwnerLookupService(self._deps.repository).execute,
            monitors=self._deps.monitors.lookup,
            validators=self._deps.validators.lookup,
            post_validators=self._deps.validators.single_entity,
        )
        bulk_owner_lookup: OwnerBulkLookupProcessor = BulkLookupActionProcessor(
            BulkFieldOwnerLookupService(self._deps.repository).execute,
            monitors=self._deps.monitors.bulk_lookup,
            post_validators=self._deps.validators.bulk,
        )
        return FieldProcessorGroup(self, owner_lookup, bulk_owner_lookup)

    def single_get_ops[TAction: GetSingleEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, EntityOpsResult[TData]]:
        self._record(action_cls)
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
        self._record(action_cls)
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
        self._record(action_cls)
        return GlobalActionProcessor(
            GlobalSearchService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )

    def global_get_ops[TAction: GetGlobalOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, EntityOpsResult[TData]]:
        self._record(action_cls)
        return GlobalActionProcessor(
            GetService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )

    def public_get_ops[TAction: GetSingleEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> PublicSingleEntityActionProcessor[TAction, EntityOpsResult[TData]]:
        self._record(action_cls)
        return PublicSingleEntityActionProcessor(
            action_cls,
            GetService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=validators,
        )

    def public_search_ops[TAction: SearchGlobalOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> PublicActionProcessor[TAction, BatchOpsResult[TData]]:
        self._record(action_cls)
        return PublicActionProcessor(
            action_cls,
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
        self._record(action_cls)
        return GlobalActionProcessor(
            GlobalCreateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )

    def global_create_with_fields_ops[TAction: CreateGlobalWithFieldsOpsAction[Any, Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, CreatedEntityWithFieldsOpsResult[TData, Any]]:
        self._record(action_cls)
        return GlobalActionProcessor(
            GlobalCreateWithFieldsService(self._deps.repository).execute,
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
        self._record(action_cls)
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
        self._record(action_cls)
        return ScopeActionProcessor(
            RoleManagedEntityCreateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(*self._deps.validators.scope, *validators),
        )

    def global_atomic_create_ops[TAction: AtomicCreateGlobalEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, EntitiesOpsResult[TData]]:
        self._record(action_cls)
        return GlobalActionProcessor(
            GlobalAtomicCreateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )

    def entity_atomic_create_ops[TAction: AtomicCreateEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, EntitiesOpsResult[TData]]:
        self._record(action_cls)
        return ScopeActionProcessor(
            EntityAtomicCreateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(*self._deps.validators.scope, *validators),
        )

    def role_managed_atomic_create_ops[TAction: AtomicCreateRoleManagedEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, EntitiesOpsResult[TData]]:
        self._record(action_cls)
        return ScopeActionProcessor(
            RoleManagedEntityAtomicCreateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(*self._deps.validators.scope, *validators),
        )

    def entity_purge_ops[TAction: PurgeEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, EntityOpsResult[TData]]:
        self._record(action_cls)
        return SingleEntityActionProcessor(
            EntityPurgeService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def global_partial_bulk_purge_ops[TAction: PartialBulkPurgeGlobalEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[BulkActionValidator] = (),
        monitors: Sequence[BulkActionMonitor] = (),
    ) -> BulkActionProcessor[TAction, BulkOpsResult[TData]]:
        self._record(action_cls)
        return BulkActionProcessor(
            GlobalPartialBulkPurgeService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.bulk, *monitors),
            validators=(*self._deps.validators.bulk, *validators),
        )

    def entity_partial_bulk_purge_ops[TAction: PartialBulkPurgeEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[BulkActionValidator] = (),
        monitors: Sequence[BulkActionMonitor] = (),
    ) -> BulkActionProcessor[TAction, BulkOpsResult[TData]]:
        self._record(action_cls)
        return BulkActionProcessor(
            EntityPartialBulkPurgeService(self._deps.repository).execute,
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
        self._record(action_cls)
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
        self._record(action_cls)
        return SingleEntityActionProcessor(
            EntityUpsertService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def entity_atomic_upsert_ops[TAction: AtomicUpsertEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, EntitiesOpsResult[TData]]:
        self._record(action_cls)
        return ScopeActionProcessor(
            EntityAtomicUpsertService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(*self._deps.validators.scope, *validators),
        )

    def global_update_ops[TAction: UpdateGlobalOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, EntityOpsResult[TData]]:
        self._record(action_cls)
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
        self._record(action_cls)
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
        self._record(action_cls)
        return SingleEntityActionProcessor(
            DeleteService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def single_restore_ops[TAction: RestoreSingleEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, EntityOpsResult[TData]]:
        self._record(action_cls)
        return SingleEntityActionProcessor(
            RestoreService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def partial_bulk_update_ops[TAction: UpdatePartialBulkOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[BulkActionValidator] = (),
        monitors: Sequence[BulkActionMonitor] = (),
    ) -> BulkActionProcessor[TAction, BulkOpsResult[TData]]:
        self._record(action_cls)
        return BulkActionProcessor(
            PartialBulkUpdateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.bulk, *monitors),
            validators=(*self._deps.validators.bulk, *validators),
        )

    def partial_bulk_delete_ops[TAction: DeletePartialBulkOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[BulkActionValidator] = (),
        monitors: Sequence[BulkActionMonitor] = (),
    ) -> BulkActionProcessor[TAction, BulkOpsResult[TData]]:
        self._record(action_cls)
        return BulkActionProcessor(
            PartialBulkDeleteService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.bulk, *monitors),
            validators=(*self._deps.validators.bulk, *validators),
        )

    def partial_bulk_restore_ops[TAction: RestorePartialBulkOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[BulkActionValidator] = (),
        monitors: Sequence[BulkActionMonitor] = (),
    ) -> BulkActionProcessor[TAction, BulkOpsResult[TData]]:
        self._record(action_cls)
        return BulkActionProcessor(
            PartialBulkRestoreService(self._deps.repository).execute,
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
        self._record(action_cls)
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
        self._record(action_cls)
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
        self._record(action_cls)
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
        self._record(action_cls)
        return GlobalActionProcessor(
            GlobalBatchPurgeService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )


class ProcessorRegistry[TData: EntityData]:
    _deps: ProcessorDependencies[TData]
    _actions: list[type[Any]]

    def __init__(self, deps: ProcessorDependencies[TData]) -> None:
        self._deps = deps
        self._actions = []

    def group(self) -> ProcessorGroup[TData]:
        return ProcessorGroup(self._deps, self._actions)

    def wired_actions(self) -> Sequence[type[Any]]:
        """Every action class wired through this registry's groups, in wiring order."""
        return tuple(self._actions)


class FieldProcessorGroup[TFieldData: FieldData]:
    """Every operation over one kind of field row.

    Reached only through :meth:`ProcessorGroup.field_group`, so the catalog cannot be
    bypassed. The field data type and the owner lookup are named once here rather than
    at every operation.
    """

    _group: ProcessorGroup[Any]
    _owner_lookup: OwnerLookupProcessor
    _bulk_owner_lookup: OwnerBulkLookupProcessor

    def __init__(
        self,
        group: ProcessorGroup[Any],
        owner_lookup: OwnerLookupProcessor,
        bulk_owner_lookup: OwnerBulkLookupProcessor,
    ) -> None:
        self._group = group
        self._owner_lookup = owner_lookup
        self._bulk_owner_lookup = bulk_owner_lookup

    def get_ops[TAction: GetFieldOpsAction[Any, Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleFieldActionProcessor[TAction, EntityOpsResult[TFieldData]]:
        self._group.record(action_cls)
        return SingleFieldActionProcessor(
            GetService(self._group.deps.repository).execute,
            self._owner_lookup,
            monitors=(*self._group.deps.monitors.single_entity, *monitors),
            validators=(*self._group.deps.validators.single_entity, *validators),
        )

    def update_ops[TAction: UpdateFieldOpsAction[Any, Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleFieldActionProcessor[TAction, EntityOpsResult[TFieldData]]:
        self._group.record(action_cls)
        return SingleFieldActionProcessor(
            UpdateService(self._group.deps.repository).execute,
            self._owner_lookup,
            monitors=(*self._group.deps.monitors.single_entity, *monitors),
            validators=(*self._group.deps.validators.single_entity, *validators),
        )

    def delete_ops[TAction: DeleteFieldOpsAction[Any, Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleFieldActionProcessor[TAction, EntityOpsResult[TFieldData]]:
        self._group.record(action_cls)
        return SingleFieldActionProcessor(
            DeleteService(self._group.deps.repository).execute,
            self._owner_lookup,
            monitors=(*self._group.deps.monitors.single_entity, *monitors),
            validators=(*self._group.deps.validators.single_entity, *validators),
        )

    def restore_ops[TAction: RestoreFieldOpsAction[Any, Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleFieldActionProcessor[TAction, EntityOpsResult[TFieldData]]:
        self._group.record(action_cls)
        return SingleFieldActionProcessor(
            RestoreService(self._group.deps.repository).execute,
            self._owner_lookup,
            monitors=(*self._group.deps.monitors.single_entity, *monitors),
            validators=(*self._group.deps.validators.single_entity, *validators),
        )

    def search_ops[TAction: OperationScopeOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, ScopedFieldsOpsResult[TFieldData]]:
        """A page of the field rows inside one owner's scope.

        Scope-shaped, like every other search that names where it looks: the owner is
        the scope, so ops applies that condition and nothing is looked up.
        """
        self._group.record(action_cls)
        return ScopeActionProcessor(
            SearchFieldsService(self._group.deps.repository).execute,
            monitors=(*self._group.deps.monitors.scope, *monitors),
            validators=(*self._group.deps.validators.scope, *validators),
        )

    def global_search_ops[TAction: SearchGlobalOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, BatchOpsResult[TFieldData]]:
        """A read across every row of this field type, behind the SUPERADMIN gate.

        For one owner's rows use :meth:`search_ops`; this one names no owner."""
        self._group.record(action_cls)
        return GlobalActionProcessor(
            GlobalSearchService(self._group.deps.repository).execute,
            monitors=(*self._group.deps.monitors.global_scope, *monitors),
            validators=(*self._group.deps.validators.global_scope, *validators),
        )

    def single_field[TAction: BaseSingleFieldAction[Any, Any], TResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleFieldActionProcessor[TAction, TResult]:
        self._group.record(action_cls)
        return SingleFieldActionProcessor(
            func,
            self._owner_lookup,
            monitors=(*self._group.deps.monitors.single_entity, *monitors),
            validators=(*self._group.deps.validators.single_entity, *validators),
        )

    def create_ops[TAction: CreateFieldOpsAction[Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, CreatedFieldOpsResult[TFieldData]]:
        self._group.record(action_cls)
        return SingleEntityActionProcessor(
            FieldCreateService(self._group.deps.repository).execute,
            monitors=(*self._group.deps.monitors.single_entity, *monitors),
            validators=(*self._group.deps.validators.single_entity, *validators),
        )

    def atomic_create_ops[TAction: AtomicCreateFieldOpsAction[Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, FieldsOpsResult[TFieldData]]:
        self._group.record(action_cls)
        return SingleEntityActionProcessor(
            FieldAtomicCreateService(self._group.deps.repository).execute,
            monitors=(*self._group.deps.monitors.single_entity, *monitors),
            validators=(*self._group.deps.validators.single_entity, *validators),
        )

    def purge_ops[TAction: PurgeFieldOpsAction[Any, Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleFieldActionProcessor[TAction, EntityOpsResult[TFieldData]]:
        self._group.record(action_cls)
        return SingleFieldActionProcessor(
            FieldPurgeService(self._group.deps.repository).execute,
            self._owner_lookup,
            monitors=(*self._group.deps.monitors.single_entity, *monitors),
            validators=(*self._group.deps.validators.single_entity, *validators),
        )

    def partial_bulk_purge_ops[TAction: PartialBulkPurgeFieldOpsAction[Any, Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[BulkActionValidator] = (),
        monitors: Sequence[BulkActionMonitor] = (),
    ) -> BulkFieldActionProcessor[TAction, TFieldData]:
        self._group.record(action_cls)
        return BulkFieldActionProcessor(
            FieldPartialBulkPurgeService(self._group.deps.repository).execute,
            self._bulk_owner_lookup,
            monitors=(*self._group.deps.monitors.bulk, *monitors),
            validators=(*self._group.deps.validators.bulk, *validators),
        )

    def upsert_ops[TAction: UpsertFieldOpsAction[Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, EntityOpsResult[TFieldData]]:
        self._group.record(action_cls)
        return SingleEntityActionProcessor(
            FieldUpsertService(self._group.deps.repository).execute,
            monitors=(*self._group.deps.monitors.single_entity, *monitors),
            validators=(*self._group.deps.validators.single_entity, *validators),
        )
