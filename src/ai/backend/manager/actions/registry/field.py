"""Every operation over one kind of field row."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from ai.backend.common.data.entity.types import EntityType, FieldData
from ai.backend.manager.actions.registry.types import (
    FieldGroupMeta,
    ProcessorDependencies,
    WiredProcessor,
)
from ai.backend.manager.actions.types import (
    ActionBacking,
    ActionGate,
    ActionKind,
)
from ai.backend.manager.actions.v2.bulk.monitor import BulkActionMonitor
from ai.backend.manager.actions.v2.bulk.validator import BulkActionValidator
from ai.backend.manager.actions.v2.field.base import BaseSingleFieldAction
from ai.backend.manager.actions.v2.field.bulk_processor import (
    BulkFieldActionProcessor,
    OwnerBulkLookupProcessor,
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
from ai.backend.manager.actions.v2.global_scope.monitor import GlobalActionMonitor
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
)
from ai.backend.manager.actions.v2.global_scope.validator import GlobalActionValidator
from ai.backend.manager.actions.v2.ops.base import (
    AtomicCreateFieldOpsAction,
    CreateFieldOpsAction,
    OperationScopeOpsAction,
    SearchGlobalOpsAction,
    UpsertFieldOpsAction,
)
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedFieldOpsResult,
    EntityOpsResult,
    FieldsOpsResult,
    ScopedFieldsOpsResult,
)
from ai.backend.manager.actions.v2.scope.monitor import ScopeActionMonitor
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.scope.validator import ScopeActionValidator
from ai.backend.manager.actions.v2.single_entity.monitor import SingleEntityActionMonitor
from ai.backend.manager.actions.v2.single_entity.processor import (
    SingleEntityActionProcessor,
)
from ai.backend.manager.actions.v2.single_entity.validator import SingleEntityActionValidator
from ai.backend.manager.services.ops.service import (
    DeleteService,
    FieldAtomicCreateService,
    FieldCreateService,
    FieldPartialBulkPurgeService,
    FieldPurgeService,
    FieldUpsertService,
    GetService,
    GlobalSearchService,
    RestoreService,
    SearchFieldsService,
    UpdateService,
)


class FieldProcessorGroup[TFieldData: FieldData]:
    """Every operation over one kind of field row.

    Reached only through :meth:`ProcessorGroup.field_group`, so the catalog cannot be
    bypassed. The field data type and the owner lookup are named once here rather than
    at every operation.
    """

    _deps: ProcessorDependencies[Any]
    _records: list[WiredProcessor]
    _concern: str
    _meta: FieldGroupMeta
    _owner_entity_type: EntityType
    _owner_lookup: OwnerLookupProcessor
    _bulk_owner_lookup: OwnerBulkLookupProcessor

    def __init__(
        self,
        deps: ProcessorDependencies[Any],
        records: list[WiredProcessor],
        concern: str,
        meta: FieldGroupMeta,
        owner_entity_type: EntityType,
        owner_lookup: OwnerLookupProcessor,
        bulk_owner_lookup: OwnerBulkLookupProcessor,
    ) -> None:
        self._deps = deps
        self._records = records
        self._concern = concern
        self._meta = meta
        self._owner_entity_type = owner_entity_type
        self._owner_lookup = owner_lookup
        self._bulk_owner_lookup = bulk_owner_lookup

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
                entity_type=self._owner_entity_type,
                field_type=self._meta.field_type,
                action_cls=action_cls,
                kind=kind,
                gate=gate,
                backing=backing,
            )
        )

    def get_ops[TAction: GetFieldOpsAction[Any, Any, Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleFieldActionProcessor[TAction, EntityOpsResult[TFieldData]]:
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION, ActionBacking.OPS)
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
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION, ActionBacking.OPS)
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
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION, ActionBacking.OPS)
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
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION, ActionBacking.OPS)
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
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION, ActionBacking.OPS)
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
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION, ActionBacking.OPS)
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
        self._record(
            action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION, ActionBacking.SERVICE
        )
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
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION, ActionBacking.OPS)
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
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION, ActionBacking.OPS)
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
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION, ActionBacking.OPS)
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
        self._record(action_cls, ActionKind.BULK, ActionGate.PERMISSION, ActionBacking.OPS)
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
        self._record(action_cls, ActionKind.SINGLE_ENTITY, ActionGate.PERMISSION, ActionBacking.OPS)
        return SingleEntityActionProcessor(
            FieldUpsertService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )
