"""What every group is handed out from."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ai.backend.common.data.entity.types import GLOBAL_ENTITY_TYPE, EntityData, FieldData
from ai.backend.manager.actions.registry.field import FieldGroup, LookupFieldGroup
from ai.backend.manager.actions.registry.group import (
    ProcessorGroup,
)
from ai.backend.manager.actions.registry.types import (
    ConcernMeta,
    FieldGroupMeta,
    GroupMeta,
    ProcessorDependencies,
    WiredProcessor,
)
from ai.backend.manager.actions.types import ActionBacking, ActionGate, ActionKind
from ai.backend.manager.actions.v2.field.bulk_lookup import (
    LookupBulkRuntimeFieldOwnerOpsAction,
)
from ai.backend.manager.actions.v2.field.bulk_processor import OwnerBulkLookupProcessor
from ai.backend.manager.actions.v2.field.lookup import LookupRuntimeFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.processor import OwnerLookupProcessor
from ai.backend.manager.actions.v2.lookup.bulk_processor import BulkLookupActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.services.ops.service import (
    BulkRuntimeFieldOwnerLookupService,
    RuntimeFieldOwnerLookupService,
)


class ConcernGroups[TData: EntityData]:
    """Every group of one area, handing out one group per entity it covers."""

    _deps: ProcessorDependencies[TData]
    _records: list[WiredProcessor]
    _concern: str

    def __init__(
        self, deps: ProcessorDependencies[TData], records: list[WiredProcessor], concern: str
    ) -> None:
        self._deps = deps
        self._records = records
        self._concern = concern

    def group(self, meta: GroupMeta) -> ProcessorGroup[TData]:
        return ProcessorGroup(self._deps, self._records, self._concern, meta)

    def dangling_field_group[TFieldData: FieldData](
        self, meta: FieldGroupMeta, data_cls: type[TFieldData]
    ) -> FieldGroup[TFieldData]:
        return FieldGroup(self._deps, self._records, self._concern, meta, GLOBAL_ENTITY_TYPE)


class ProcessorRegistry[TData: EntityData]:
    _deps: ProcessorDependencies[TData]
    _records: list[WiredProcessor]

    def __init__(self, deps: ProcessorDependencies[TData]) -> None:
        self._deps = deps
        self._records = []

    def concern(self, meta: ConcernMeta) -> ConcernGroups[TData]:
        """The groups of one area, so every wiring made through them names it."""
        return ConcernGroups(self._deps, self._records, meta.name)

    def group(self, meta: GroupMeta) -> ProcessorGroup[TData]:
        """A group for a domain that is its own area, which its entity type names."""
        return ProcessorGroup(self._deps, self._records, meta.entity_type, meta)

    def dangling_field_group[TFieldData: FieldData](
        self, meta: FieldGroupMeta, data_cls: type[TFieldData]
    ) -> FieldGroup[TFieldData]:
        """The operations over a field kind whose owner is not fixed.

        Reached from the registry rather than an entity group, unlike
        :meth:`ProcessorGroup.field_group`: the owner's type is a value on the row, and
        some rows have no owner at all.
        """
        return FieldGroup(self._deps, self._records, meta.field_type, meta, GLOBAL_ENTITY_TYPE)

    def dangling_lookup_field_group[TFieldData: FieldData](
        self,
        meta: FieldGroupMeta,
        data_cls: type[TFieldData],
        owner_lookup_action_cls: type[LookupRuntimeFieldOwnerOpsAction[Any]],
        bulk_owner_lookup_action_cls: type[LookupBulkRuntimeFieldOwnerOpsAction[Any]],
    ) -> LookupFieldGroup[TFieldData]:
        """The operations over a field kind whose owner is not fixed, including the ones
        that name a single row.

        :meth:`dangling_field_group` with the owner lookups built, so a row can be named
        by its own id: the lookup reads the type beside the id, and the operation that
        follows is answered for by the entity both name.
        """
        self._record_lookup(meta, owner_lookup_action_cls)
        self._record_lookup(meta, bulk_owner_lookup_action_cls)
        owner_lookup: OwnerLookupProcessor = LookupActionProcessor(
            RuntimeFieldOwnerLookupService(self._deps.repository).execute,
            monitors=self._deps.monitors.lookup,
            validators=self._deps.validators.lookup,
            post_validators=self._deps.validators.single_entity,
        )
        bulk_owner_lookup: OwnerBulkLookupProcessor = BulkLookupActionProcessor(
            BulkRuntimeFieldOwnerLookupService(self._deps.repository).execute,
            monitors=self._deps.monitors.bulk_lookup,
            post_validators=self._deps.validators.atomic_bulk,
        )
        return LookupFieldGroup(
            self._deps,
            self._records,
            meta.field_type,
            meta,
            GLOBAL_ENTITY_TYPE,
            owner_lookup,
            bulk_owner_lookup,
        )

    def _record_lookup(self, meta: FieldGroupMeta, action_cls: type[Any]) -> None:
        self._records.append(
            WiredProcessor(
                concern=meta.field_type,
                entity_type=GLOBAL_ENTITY_TYPE,
                field_type=meta.field_type,
                action_cls=action_cls,
                kind=ActionKind.LOOKUP,
                gate=ActionGate.PERMISSION,
                backing=ActionBacking.GENERIC,
            )
        )

    def wired_processors(self) -> Sequence[WiredProcessor]:
        """Every wiring made through this registry's groups, in wiring order."""
        return tuple(self._records)

    def wired_actions(self) -> Sequence[type[Any]]:
        """Every action class wired through this registry's groups, in wiring order."""
        return tuple(r.action_cls for r in self._records)
