from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import DeleteSingleEntityOpsAction
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.specs.soft_delete import SoftDeleteUpdater
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow

__all__ = ("DeleteSystemSessionEnvironAction",)


@dataclass(frozen=True)
class DeleteSystemSessionEnvironAction(
    DeleteSingleEntityOpsAction[SystemSessionEnvironRow, SystemSessionEnvironData]
):
    """Soft-delete a system session environ row; sessions started afterwards no longer
    receive it."""

    updater: SoftDeleteUpdater[SystemSessionEnvironRow, SystemSessionEnvironData]

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.target_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_system_session_environ"

    @override
    def to_updater(self) -> SoftDeleteUpdater[SystemSessionEnvironRow, SystemSessionEnvironData]:
        return self.updater
