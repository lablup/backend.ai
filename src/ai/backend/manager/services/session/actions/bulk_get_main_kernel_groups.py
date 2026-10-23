from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetOwnedFieldOpsAction
from ai.backend.manager.data.kernel_group.types import KernelGroupData
from ai.backend.manager.models.kernel_group.queriers import MainKernelGroupQuerier
from ai.backend.manager.models.kernel_group.row import KernelGroupRow


@dataclass(frozen=True)
class BulkGetMainKernelGroupsAction(
    PartialBulkGetOwnedFieldOpsAction[SessionID, KernelGroupRow, KernelGroupData]
):
    """Read the main kernel group of each session the caller named, answering for each one."""

    session_ids: Sequence[SessionID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_main_kernel_groups"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.session_ids)

    @override
    def owner_ids(self) -> Sequence[SessionID]:
        return tuple(self.session_ids)

    @override
    def to_querier(self) -> MainKernelGroupQuerier:
        return MainKernelGroupQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, session_ids=[sid for sid in self.session_ids if sid in allowed])
