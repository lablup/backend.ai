from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.kernel.types import KernelSchedulingHistoryData
from ai.backend.manager.models.scheduling_history.row import KernelSchedulingHistoryRow


@dataclass(frozen=True)
class SearchKernelHistoryAction(
    GlobalSearcherOpsAction[KernelSchedulingHistoryRow, KernelSchedulingHistoryData]
):
    """Page through every kernel scheduling history row."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_kernel_history"
