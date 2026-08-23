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
from typing import Any

from ai.backend.common.data.entity.types import EntityData, FieldData
from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.registry.types import (
    FieldGroupMeta,
    GroupMeta,
    ProcessorDependencies,
    WiredProcessor,
)
from ai.backend.manager.actions.types import (
    ActionBacking,
    ActionGate,
    ActionKind,
    ActionOperationType,
)
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.bulk.monitor import BulkActionMonitor
from ai.backend.manager.actions.v2.bulk.processor import (
    BulkActionProcessor,
    PartialEntityResultJudge,
)
from ai.backend.manager.actions.v2.bulk.result import BasePartialBulkActionResult
from ai.backend.manager.actions.v2.bulk.validator import BulkActionValidator
from ai.backend.manager.actions.v2.field.bulk_base import BaseBulkFieldAction
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.bulk_processor import (
    AtomicFieldResultJudge,
    BulkFieldActionProcessor,
    OwnerBulkLookupProcessor,
)
from ai.backend.manager.actions.v2.field.lookup import (
    LookupFieldOwnerByKeyOpsAction,
    LookupFieldOwnerOpsAction,
)
from ai.backend.manager.actions.v2.field.processor import (
    OwnerLookupProcessor,
)
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.monitor import GlobalActionMonitor
from ai.backend.manager.actions.v2.global_scope.processor import (
    AnonymousGlobalActionProcessor,
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
    AtomicCreateGlobalEntityOpsAction,
    AtomicCreateRoleManagedEntityOpsAction,
    AtomicUpsertEntityOpsAction,
    AtomicUpsertGlobalEntityOpsAction,
    BatchPurgeGlobalOpsAction,
    BatchPurgeScopeOpsAction,
    BatchUpdateGlobalOpsAction,
    BatchUpdateScopeOpsAction,
    CreateEntityOpsAction,
    CreateEntityWithFieldsOpsAction,
    CreateGlobalOpsAction,
    CreateGlobalRoleManagedEntityOpsAction,
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
    UpsertGlobalOpsAction,
)
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    BulkOpsResult,
    CreatedEntityOpsResult,
    CreatedEntityWithFieldsOpsResult,
    EntitiesOpsResult,
    EntityOpsResult,
    FieldOwnerLookupOpsResult,
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
from ai.backend.manager.actions.v2.single_entity.processor import (
    PublicSingleEntityActionProcessor,
    SingleEntityActionProcessor,
)
from ai.backend.manager.actions.v2.single_entity.validator import SingleEntityActionValidator
from ai.backend.manager.errors.common import ServerMisconfiguredError
from ai.backend.manager.services.ops.service import (
    BatchPurgeService,
    BatchUpdateService,
    BulkFieldOwnerLookupService,
    DeleteService,
    EntityAtomicCreateService,
    EntityAtomicUpsertService,
    EntityCreateService,
    EntityCreateWithFieldsService,
    EntityPartialBulkPurgeService,
    EntityPurgeService,
    EntityUpsertService,
    FieldOwnerKeyLookupService,
    FieldOwnerLookupService,
    GetService,
    GlobalAtomicCreateService,
    GlobalAtomicUpsertService,
    GlobalBatchPurgeService,
    GlobalBatchUpdateService,
    GlobalCreateService,
    GlobalCreateWithFieldsService,
    GlobalPartialBulkPurgeService,
    GlobalRoleManagedEntityCreateService,
    GlobalSearchService,
    GlobalUpsertService,
    LookupService,
    PartialBulkDeleteService,
    PartialBulkRestoreService,
    PartialBulkUpdateService,
    RestoreService,
    RoleManagedEntityAtomicCreateService,
    RoleManagedEntityCreateService,
    SearchService,
    UpdateService,
)


class ProcessorGroup[TData: EntityData]:
    _deps: ProcessorDependencies[TData]
    _records: list[WiredProcessor]
    _concern: str
    _meta: GroupMeta

    def __init__(
        self,
        deps: ProcessorDependencies[TData],
        records: list[WiredProcessor],
        concern: str,
        meta: GroupMeta,
    ) -> None:
        self._deps = deps
        self._records = records
        self._concern = concern
        self._meta = meta

    @property
    def deps(self) -> ProcessorDependencies[TData]:
        """Read by :class:`LookupFieldGroup`, which builds processors of this group."""
        return self._deps

    @property
    def concern(self) -> str:
        """Read by :class:`LookupFieldGroup`, whose rows sit in the same area."""
        return self._concern

    @property
    def meta(self) -> GroupMeta:
        """Read by :class:`LookupFieldGroup`, whose rows name this group as the owner."""
        return self._meta

    def record(
        self,
        action_cls: type[Any],
        kind: ActionKind,
        gate: ActionGate,
        backing: ActionBacking,
    ) -> None:
        """Record a wiring made by a sub-group, so one catalog holds them all."""
        self._record(action_cls, kind, gate, backing)

    def _record(
        self,
        action_cls: type[Any],
        kind: ActionKind,
        gate: ActionGate,
        backing: ActionBacking,
    ) -> None:
        self._records.append(
            WiredProcessor(
                concern=self._concern,
                entity_type=self._meta.entity_type,
                field_type=None,
                action_cls=action_cls,
                kind=kind,
                gate=gate,
                backing=backing,
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
        self._record(
            action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION, ActionBacking.CUSTOM
        )
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION, ActionBacking.CUSTOM)
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.ANONYMOUS, ActionBacking.CUSTOM)
        return ScopeActionProcessor(
            func,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(),
        )

    def bulk[TAction: BaseBulkAction, TResult: BasePartialBulkActionResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[BulkActionValidator] = (),
        monitors: Sequence[BulkActionMonitor] = (),
    ) -> BulkActionProcessor[TAction, TResult]:
        self._record(action_cls, ActionKind.BULK, ActionGate.PERMISSION, ActionBacking.CUSTOM)
        return BulkActionProcessor(
            func,
            PartialEntityResultJudge(),
            monitors=(*self._deps.monitors.bulk, *monitors),
            validators=(*self._deps.validators.bulk, *validators),
        )

    def atomic_bulk_field[TAction: BaseBulkFieldAction[Any, Any], TResult](
        self,
        action_cls: type[TAction],
        bulk_owner_lookup_action_cls: type[LookupBulkFieldOwnerOpsAction[Any, Any]],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[BulkActionValidator] = (),
        monitors: Sequence[BulkActionMonitor] = (),
    ) -> BulkFieldActionProcessor[TAction, TResult]:
        """Several field rows read by a service, answered for by the entities owning them.

        Reached from this group rather than the one :meth:`field_group` hands out: that
        one is typed by the ``FieldData`` its ops operations return, and a read backed by
        a service returns its own result instead. The owner lookup is built here for the
        same reason it is built there -- it is the step the operation runs first, not an
        operation a domain wires.

        The run stands or falls as one, so every owner read shares its outcome.
        """
        self._record(action_cls, ActionKind.BULK, ActionGate.PERMISSION, ActionBacking.CUSTOM)
        self._record(
            bulk_owner_lookup_action_cls,
            ActionKind.LOOKUP,
            ActionGate.PERMISSION,
            ActionBacking.GENERIC,
        )
        bulk_owner_lookup: OwnerBulkLookupProcessor = BulkLookupActionProcessor(
            BulkFieldOwnerLookupService(self._deps.repository).execute,
            monitors=self._deps.monitors.bulk_lookup,
            post_validators=self._deps.validators.bulk,
        )
        return BulkFieldActionProcessor(
            func,
            bulk_owner_lookup,
            AtomicFieldResultJudge(),
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PUBLIC, ActionBacking.CUSTOM)
        return PublicActionProcessor(
            action_cls,
            func,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=list(validators),
        )

    def anonymous_global[TAction: BaseGlobalAction, TResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> AnonymousGlobalActionProcessor[TAction, TResult]:
        """Global state reached with no gate at all, writes included.

        Discouraged: every other factory is a better answer. This one exists for the
        caller that can never hold a principal -- an external system posting to a
        webhook -- where the operation checks that caller itself against a secret the
        entity stores. Nothing here verifies that it does, so read the service before
        wiring one.

        The catalog records the wiring as an anonymous gate, which is how the ungated
        writes stay countable.
        """
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.ANONYMOUS, ActionBacking.CUSTOM)
        return AnonymousGlobalActionProcessor(
            func,
            monitors=(*self._deps.monitors.global_scope, *monitors),
        )

    def global_scope[TAction: BaseGlobalAction, TResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, TResult]:
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION, ActionBacking.CUSTOM)
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
        self._record(action_cls, ActionKind.LOOKUP, ActionGate.PERMISSION, ActionBacking.CUSTOM)
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
    ) -> LookupActionProcessor[TAction, LookupOpsResult[Any]]:
        self._record(action_cls, ActionKind.LOOKUP, ActionGate.PERMISSION, ActionBacking.GENERIC)
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
    ) -> LookupActionProcessor[TAction, LookupOpsResult[Any]]:
        """A key every authenticated caller may resolve: no post-validators, so the
        resolved entity carries no permission."""
        self._record(action_cls, ActionKind.LOOKUP, ActionGate.PUBLIC, ActionBacking.GENERIC)
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
        self._record(action_cls, ActionKind.LOOKUP, ActionGate.PERMISSION, ActionBacking.GENERIC)
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
    ) -> LookupFieldGroup[TFieldData]:
        """The operations over one kind of field row.

        Builds the owner lookups itself: they are not operations a domain wires, only
        the step every field operation runs first — one row at a time or many. A kind
        """
        self._record(
            owner_lookup_action_cls, ActionKind.LOOKUP, ActionGate.PERMISSION, ActionBacking.GENERIC
        )
        self._record(
            bulk_owner_lookup_action_cls,
            ActionKind.LOOKUP,
            ActionGate.PERMISSION,
            ActionBacking.GENERIC,
        )
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
        return LookupFieldGroup(
            self._deps,
            self._records,
            self._concern,
            meta,
            self._meta.entity_type,
            owner_lookup,
            bulk_owner_lookup,
        )

    def single_get_ops[TAction: GetSingleEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, EntityOpsResult[TData]]:
        self._record(
            action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION, ActionBacking.GENERIC
        )
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION, ActionBacking.GENERIC)
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION, ActionBacking.GENERIC)
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION, ActionBacking.GENERIC)
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
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PUBLIC, ActionBacking.GENERIC)
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PUBLIC, ActionBacking.GENERIC)
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION, ActionBacking.GENERIC)
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION, ActionBacking.GENERIC)
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION, ActionBacking.GENERIC)
        return ScopeActionProcessor(
            EntityCreateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(*self._deps.validators.scope, *validators),
        )

    def entity_create_with_fields_ops[TAction: CreateEntityWithFieldsOpsAction[Any, Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, CreatedEntityWithFieldsOpsResult[TData, Any]]:
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION, ActionBacking.GENERIC)
        return ScopeActionProcessor(
            EntityCreateWithFieldsService(self._deps.repository).execute,
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION, ActionBacking.GENERIC)
        return ScopeActionProcessor(
            RoleManagedEntityCreateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(*self._deps.validators.scope, *validators),
        )

    def global_role_managed_create_ops[TAction: CreateGlobalRoleManagedEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, CreatedEntityOpsResult[TData]]:
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION, ActionBacking.GENERIC)
        return GlobalActionProcessor(
            GlobalRoleManagedEntityCreateService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )

    def global_atomic_create_ops[TAction: AtomicCreateGlobalEntityOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, EntitiesOpsResult[TData]]:
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION, ActionBacking.GENERIC)
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION, ActionBacking.GENERIC)
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION, ActionBacking.GENERIC)
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
        self._record(
            action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION, ActionBacking.GENERIC
        )
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
        self._record(action_cls, ActionKind.BULK, ActionGate.PERMISSION, ActionBacking.GENERIC)
        return BulkActionProcessor(
            GlobalPartialBulkPurgeService(self._deps.repository).execute,
            PartialEntityResultJudge(),
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
        self._record(action_cls, ActionKind.BULK, ActionGate.PERMISSION, ActionBacking.GENERIC)
        return BulkActionProcessor(
            EntityPartialBulkPurgeService(self._deps.repository).execute,
            PartialEntityResultJudge(),
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION, ActionBacking.GENERIC)
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
        self._record(
            action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION, ActionBacking.GENERIC
        )
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION, ActionBacking.GENERIC)
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION, ActionBacking.GENERIC)
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION, ActionBacking.GENERIC)
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
        self._record(
            action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION, ActionBacking.GENERIC
        )
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
        self._record(
            action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION, ActionBacking.GENERIC
        )
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
        self._record(
            action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION, ActionBacking.GENERIC
        )
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
        self._record(action_cls, ActionKind.BULK, ActionGate.PERMISSION, ActionBacking.GENERIC)
        return BulkActionProcessor(
            PartialBulkUpdateService(self._deps.repository).execute,
            PartialEntityResultJudge(),
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
        self._record(action_cls, ActionKind.BULK, ActionGate.PERMISSION, ActionBacking.GENERIC)
        return BulkActionProcessor(
            PartialBulkDeleteService(self._deps.repository).execute,
            PartialEntityResultJudge(),
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
        self._record(action_cls, ActionKind.BULK, ActionGate.PERMISSION, ActionBacking.GENERIC)
        return BulkActionProcessor(
            PartialBulkRestoreService(self._deps.repository).execute,
            PartialEntityResultJudge(),
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION, ActionBacking.GENERIC)
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION, ActionBacking.GENERIC)
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION, ActionBacking.GENERIC)
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION, ActionBacking.GENERIC)
        return GlobalActionProcessor(
            GlobalBatchPurgeService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )
