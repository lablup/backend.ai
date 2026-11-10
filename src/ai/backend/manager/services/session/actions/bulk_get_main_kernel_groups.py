from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import BulkGetOwnedFieldOpsAction
from ai.backend.manager.data.kernel_group.types import KernelGroupData
from ai.backend.manager.models.kernel_group.queriers import MainKernelGroupQuerier
from ai.backend.manager.models.kernel_group.row import KernelGroupRow


@dataclass(frozen=True)
class BulkGetMainKernelGroupsAction(
    BulkGetOwnedFieldOpsAction[SessionID, KernelGroupRow, KernelGroupData]
):
    """Read the main kernel group of each session the caller named."""

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
