"""What every group is handed out from."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ai.backend.common.data.entity.types import EntityData
from ai.backend.manager.actions.registry.group import (
    ProcessorGroup,
)
from ai.backend.manager.actions.registry.sidecar import (
    SidecarProcessorGroup,
)
from ai.backend.manager.actions.registry.types import (
    ConcernMeta,
    GroupMeta,
    ProcessorDependencies,
    SidecarGroupMeta,
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

    def sidecar_group[TSidecarData](
        self, meta: SidecarGroupMeta, data_cls: type[TSidecarData]
    ) -> SidecarProcessorGroup[TSidecarData]:
        return SidecarProcessorGroup(self._deps, self._records, self._concern, meta)


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

    def sidecar_group[TSidecarData](
        self, meta: SidecarGroupMeta, data_cls: type[TSidecarData]
    ) -> SidecarProcessorGroup[TSidecarData]:
        """The reads over one kind of sidecar row.

        Reached from the registry rather than an entity group, unlike
        :meth:`ProcessorGroup.field_group`: a sidecar belongs to no entity.
        """
        return SidecarProcessorGroup(self._deps, self._records, meta.entity_type, meta)

    def wired_processors(self) -> Sequence[WiredProcessor]:
        """Every wiring made through this registry's groups, in wiring order."""
        return tuple(self._records)

    def wired_actions(self) -> Sequence[type[Any]]:
        """Every action class wired through this registry's groups, in wiring order."""
        return tuple(r.action_cls for r in self._records)
