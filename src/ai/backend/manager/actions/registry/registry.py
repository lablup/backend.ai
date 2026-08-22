"""What every group is handed out from."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ai.backend.common.data.entity.types import GLOBAL_ENTITY_TYPE, EntityData, FieldData
from ai.backend.manager.actions.registry.field import FieldGroup
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

    def wired_processors(self) -> Sequence[WiredProcessor]:
        """Every wiring made through this registry's groups, in wiring order."""
        return tuple(self._records)

    def wired_actions(self) -> Sequence[type[Any]]:
        """Every action class wired through this registry's groups, in wiring order."""
        return tuple(r.action_cls for r in self._records)
