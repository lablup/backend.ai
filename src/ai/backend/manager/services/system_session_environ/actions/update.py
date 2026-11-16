from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdateSingleEntityOpsAction
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow
from ai.backend.manager.models.system_session_environ.updaters import (
    SystemSessionEnvironUpdater,
)

__all__ = ("UpdateSystemSessionEnvironAction",)


@dataclass(frozen=True)
class UpdateSystemSessionEnvironAction(
    UpdateSingleEntityOpsAction[SystemSessionEnvironRow, SystemSessionEnvironData]
):
    """Rename a system session environ row's key."""

    updater: SystemSessionEnvironUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_system_session_environ"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.environ_id

    @override
    def to_updater(self) -> SystemSessionEnvironUpdater:
        return self.updater
