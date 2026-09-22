from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.models.kernel.row import KernelRow


@dataclass(frozen=True)
class GlobalSearchKernelsAction(GlobalSearcherOpsAction[KernelRow, KernelInfo]):
    """Page through the kernels of every session."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_kernels"
