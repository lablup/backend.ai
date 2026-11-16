from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import RestoreSingleEntityOpsAction
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.specs.soft_delete import RestoreUpdater
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow

__all__ = ("RestoreSystemSessionEnvironAction",)


@dataclass(frozen=True)
class RestoreSystemSessionEnvironAction(
    RestoreSingleEntityOpsAction[SystemSessionEnvironRow, SystemSessionEnvironData]
):
    """Bring a soft-deleted system session environ row back."""

    updater: RestoreUpdater[SystemSessionEnvironRow, SystemSessionEnvironData]

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.target_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "restore_system_session_environ"

    @override
    def to_updater(self) -> RestoreUpdater[SystemSessionEnvironRow, SystemSessionEnvironData]:
        return self.updater
