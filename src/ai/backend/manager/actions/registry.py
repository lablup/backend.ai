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

from ai.backend.common.data.entity.types import EntityData, EntityType, FieldData, FieldType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.types import ActionGate, ActionKind, ActionOperationType
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
from ai.backend.manager.actions.v2.field.lookup import (
    LookupFieldOwnerByKeyOpsAction,
    LookupFieldOwnerOpsAction,
)
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
    AtomicUpsertGlobalEntityOpsAction,
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
    FieldOwnerLookupOpsResult,
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
    FieldOwnerKeyLookupService,
    FieldOwnerLookupService,
    FieldPartialBulkPurgeService,
    FieldPurgeService,
    FieldUpsertService,
    GetService,
    GlobalAtomicCreateService,
    GlobalAtomicUpsertService,
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
    "GroupMeta",
    "FieldGroupMeta",
    "SidecarGroupMeta",
    "WiredProcessor",
    "ProcessorGroup",
    "FieldProcessorGroup",
    "SidecarProcessorGroup",
    "ProcessorRegistry",
)


@dataclass(frozen=True)
class ProcessorDependencies[TData: EntityData]:
    monitors: ActionMonitors
    validators: ActionValidators
    repository: OpsRepository[TData]


@dataclass(frozen=True)
class GroupMeta:
    """What every operation of one group is answered for."""

    entity_type: EntityType


@dataclass(frozen=True)
class FieldGroupMeta:
    """What every operation of one field group is answered for.

    Names the field's own type; the entity owning it is the parent group's.
    """

    field_type: FieldType


@dataclass(frozen=True)
class SidecarGroupMeta:
    """What every read of one sidecar group is answered for."""

    entity_type: EntityType


@dataclass(frozen=True)
class WiredProcessor:
    """One wiring call, as the catalog records it.

    The action class carries what it declares — the operation, the action name, whether
    it runs against ops. What only the wiring knows is here.
    """

    entity_type: EntityType
    # Set when the operation is over a field row, whose owner ``entity_type`` names.
    field_type: FieldType | None
    action_cls: type[Any]
    kind: ActionKind
    gate: ActionGate


class ProcessorGroup[TData: EntityData]:
    _deps: ProcessorDependencies[TData]
    _records: list[WiredProcessor]
    _meta: GroupMeta

    def __init__(
        self,
        deps: ProcessorDependencies[TData],
        records: list[WiredProcessor],
        meta: GroupMeta,
    ) -> None:
        self._deps = deps
        self._records = records
        self._meta = meta

    @property
    def deps(self) -> ProcessorDependencies[TData]:
        """Read by :class:`FieldProcessorGroup`, which builds processors of this group."""
        return self._deps

    @property
    def meta(self) -> GroupMeta:
        """Read by :class:`FieldProcessorGroup`, whose rows name this group as the owner."""
        return self._meta

    def record(self, action_cls: type[Any], kind: ActionKind, gate: ActionGate) -> None:
        """Record a wiring made by a sub-group, so one catalog holds them all."""
        self._record(action_cls, kind, gate)

    def _record(self, action_cls: type[Any], kind: ActionKind, gate: ActionGate) -> None:
        self._records.append(
            WiredProcessor(
                entity_type=self._meta.entity_type,
                field_type=None,
                action_cls=action_cls,
                kind=kind,
                gate=gate,
            )
        )

    def single_entity[TAction: BaseSingleEntityAction, TResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, TResult]:
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.ANONYMOUS)
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
        self._record(action_cls, ActionKind.BULK, ActionGate.PERMISSION)
        return BulkActionProcessor(
            func,
            monitors=(*self._deps.monitors.bulk, *monitors),
            validators=(*self._deps.validators.bulk, *validators),
        )

    def public[TAction: BaseGlobalAction, TResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> PublicActionProcessor[TAction, TResult]:
        """Global state every authenticated caller may read.

        The SUPERADMIN gate is replaced by an authentication check; the constructor
        rejects anything that is not a read, so a write cannot reach this path.
        """
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PUBLIC)
        return PublicActionProcessor(
            action_cls,
            func,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=list(validators),
        )

    def global_scope[TAction: BaseGlobalAction, TResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, TResult]:
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.LOOKUP, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.LOOKUP, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.LOOKUP, ActionGate.PUBLIC)
        return LookupActionProcessor(
            LookupService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.lookup, *monitors),
            validators=(*self._deps.validators.lookup, *validators),
        )

    def key_owner_lookup_ops[TAction: LookupFieldOwnerByKeyOpsAction[Any]](
        self,
        action_cls: type[TAction],
        *,
        monitors: Sequence[LookupActionMonitor] = (),
    ) -> LookupActionProcessor[TAction, FieldOwnerLookupOpsResult]:
        """The owner of the field row a caller-facing key names.

        Authentication is the only gate, as with every lookup: what the key resolved to
        is what the operation following it is checked against.
        """
        self._record(action_cls, ActionKind.LOOKUP, ActionGate.PERMISSION)
        return LookupActionProcessor(
            FieldOwnerKeyLookupService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.lookup, *monitors),
            validators=self._deps.validators.lookup,
            post_validators=(),
        )

    def field_group[TFieldData: FieldData](
        self,
        meta: FieldGroupMeta,
        data_cls: type[TFieldData],
        owner_lookup_action_cls: type[LookupFieldOwnerOpsAction[Any, Any]],
        bulk_owner_lookup_action_cls: type[LookupBulkFieldOwnerOpsAction[Any, Any]],
    ) -> FieldProcessorGroup[TFieldData]:
        """The operations over one kind of field row.

        Builds the owner lookups itself: they are not operations a domain wires, only
        the step every field operation runs first — one row at a time or many.
        """
        self._record(owner_lookup_action_cls, ActionKind.LOOKUP, ActionGate.PERMISSION)
        self._record(bulk_owner_lookup_action_cls, ActionKind.LOOKUP, ActionGate.PERMISSION)
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
        return FieldProcessorGroup(
            self._deps, self._records, meta, self._meta.entity_type, owner_lookup, bulk_owner_lookup
        )

    def single_get_ops[TAction: GetSingleEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, EntityOpsResult[TData]]:
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PUBLIC)
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PUBLIC)
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.BULK, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.BULK, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION)
        return SingleEntityActionProcessor(
            EntityUpsertService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def global_atomic_upsert_ops[TAction: AtomicUpsertGlobalEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, EntitiesOpsResult[TData]]:
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION)
        return GlobalActionProcessor(
            GlobalAtomicUpsertService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )

    def entity_atomic_upsert_ops[TAction: AtomicUpsertEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, EntitiesOpsResult[TData]]:
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.BULK, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.BULK, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.BULK, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION)
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION)
        return GlobalActionProcessor(
            GlobalBatchPurgeService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )


class SidecarProcessorGroup[TSidecarData]:
    """The reads over one kind of sidecar row.

    A sidecar stands outside the graph, so there is no create or purge here — those go
    through the repository, which is where the writers of such rows already are. What is
    here is the two reads, and both report no entity: a sidecar row is not one.
    """

    _deps: ProcessorDependencies[Any]
    _records: list[WiredProcessor]
    _meta: SidecarGroupMeta

    def __init__(
        self,
        deps: ProcessorDependencies[Any],
        records: list[WiredProcessor],
        meta: SidecarGroupMeta,
    ) -> None:
        self._deps = deps
        self._records = records
        self._meta = meta

    def _record(self, action_cls: type[Any], kind: ActionKind, gate: ActionGate) -> None:
        self._records.append(
            WiredProcessor(
                entity_type=self._meta.entity_type,
                field_type=None,
                action_cls=action_cls,
                kind=kind,
                gate=gate,
            )
        )

    def search_ops[TAction: OperationScopeOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, ScopedFieldsOpsResult[TSidecarData]]:
        """A page of the sidecar rows inside the scopes the action names.

        Scope-shaped like every other search that names where it looks, and the scope's
        condition is written against the row's own columns — there is no owner to look up.
        """
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION)
        return ScopeActionProcessor(
            SearchFieldsService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(*self._deps.validators.scope, *validators),
        )

    def global_search_ops[TAction: SearchGlobalOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, BatchOpsResult[TSidecarData]]:
        """A read across every row of this sidecar type, behind the SUPERADMIN gate.

        For the rows of named scopes use :meth:`search_ops`; this one names none."""
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION)
        return GlobalActionProcessor(
            GlobalSearchService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )


class ProcessorRegistry[TData: EntityData]:
    _deps: ProcessorDependencies[TData]
    _records: list[WiredProcessor]

    def __init__(self, deps: ProcessorDependencies[TData]) -> None:
        self._deps = deps
        self._records = []

    def group(self, meta: GroupMeta) -> ProcessorGroup[TData]:
        return ProcessorGroup(self._deps, self._records, meta)

    def sidecar_group[TSidecarData](
        self, meta: SidecarGroupMeta, data_cls: type[TSidecarData]
    ) -> SidecarProcessorGroup[TSidecarData]:
        """The reads over one kind of sidecar row.

        Reached from the registry rather than an entity group, unlike
        :meth:`ProcessorGroup.field_group`: a sidecar belongs to no entity.
        """
        return SidecarProcessorGroup(self._deps, self._records, meta)

    def wired_processors(self) -> Sequence[WiredProcessor]:
        """Every wiring made through this registry's groups, in wiring order."""
        return tuple(self._records)

    def wired_actions(self) -> Sequence[type[Any]]:
        """Every action class wired through this registry's groups, in wiring order."""
        return tuple(r.action_cls for r in self._records)


class FieldProcessorGroup[TFieldData: FieldData]:
    """Every operation over one kind of field row.

    Reached only through :meth:`ProcessorGroup.field_group`, so the catalog cannot be
    bypassed. The field data type and the owner lookup are named once here rather than
    at every operation.
    """

    _deps: ProcessorDependencies[Any]
    _records: list[WiredProcessor]
    _meta: FieldGroupMeta
    _owner_entity_type: EntityType
    _owner_lookup: OwnerLookupProcessor
    _bulk_owner_lookup: OwnerBulkLookupProcessor

    def __init__(
        self,
        deps: ProcessorDependencies[Any],
        records: list[WiredProcessor],
        meta: FieldGroupMeta,
        owner_entity_type: EntityType,
        owner_lookup: OwnerLookupProcessor,
        bulk_owner_lookup: OwnerBulkLookupProcessor,
    ) -> None:
        self._deps = deps
        self._records = records
        self._meta = meta
        self._owner_entity_type = owner_entity_type
        self._owner_lookup = owner_lookup
        self._bulk_owner_lookup = bulk_owner_lookup

    def _record(self, action_cls: type[Any], kind: ActionKind, gate: ActionGate) -> None:
        self._records.append(
            WiredProcessor(
                entity_type=self._owner_entity_type,
                field_type=self._meta.field_type,
                action_cls=action_cls,
                kind=kind,
                gate=gate,
            )
        )

    def get_ops[TAction: GetFieldOpsAction[Any, Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleFieldActionProcessor[TAction, EntityOpsResult[TFieldData]]:
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION)
        return SingleFieldActionProcessor(
            GetService(self._deps.repository).execute,
            self._owner_lookup,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def update_ops[TAction: UpdateFieldOpsAction[Any, Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleFieldActionProcessor[TAction, EntityOpsResult[TFieldData]]:
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION)
        return SingleFieldActionProcessor(
            UpdateService(self._deps.repository).execute,
            self._owner_lookup,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def delete_ops[TAction: DeleteFieldOpsAction[Any, Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleFieldActionProcessor[TAction, EntityOpsResult[TFieldData]]:
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION)
        return SingleFieldActionProcessor(
            DeleteService(self._deps.repository).execute,
            self._owner_lookup,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def restore_ops[TAction: RestoreFieldOpsAction[Any, Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleFieldActionProcessor[TAction, EntityOpsResult[TFieldData]]:
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION)
        return SingleFieldActionProcessor(
            RestoreService(self._deps.repository).execute,
            self._owner_lookup,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION)
        return ScopeActionProcessor(
            SearchFieldsService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(*self._deps.validators.scope, *validators),
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION)
        return GlobalActionProcessor(
            GlobalSearchService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )

    def single_field[TAction: BaseSingleFieldAction[Any, Any], TResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleFieldActionProcessor[TAction, TResult]:
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION)
        return SingleFieldActionProcessor(
            func,
            self._owner_lookup,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def create_ops[TAction: CreateFieldOpsAction[Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, CreatedFieldOpsResult[TFieldData]]:
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION)
        return SingleEntityActionProcessor(
            FieldCreateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def atomic_create_ops[TAction: AtomicCreateFieldOpsAction[Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, FieldsOpsResult[TFieldData]]:
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION)
        return SingleEntityActionProcessor(
            FieldAtomicCreateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def purge_ops[TAction: PurgeFieldOpsAction[Any, Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleFieldActionProcessor[TAction, EntityOpsResult[TFieldData]]:
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION)
        return SingleFieldActionProcessor(
            FieldPurgeService(self._deps.repository).execute,
            self._owner_lookup,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def partial_bulk_purge_ops[TAction: PartialBulkPurgeFieldOpsAction[Any, Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[BulkActionValidator] = (),
        monitors: Sequence[BulkActionMonitor] = (),
    ) -> BulkFieldActionProcessor[TAction, TFieldData]:
        self._record(action_cls, ActionKind.BULK, ActionGate.PERMISSION)
        return BulkFieldActionProcessor(
            FieldPartialBulkPurgeService(self._deps.repository).execute,
            self._bulk_owner_lookup,
            monitors=(*self._deps.monitors.bulk, *monitors),
            validators=(*self._deps.validators.bulk, *validators),
        )

    def upsert_ops[TAction: UpsertFieldOpsAction[Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, EntityOpsResult[TFieldData]]:
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION)
        return SingleEntityActionProcessor(
            FieldUpsertService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )
