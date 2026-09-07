from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.idle_checker import IDLE_CHECKER_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import UpdateGlobalOpsAction
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow
from ai.backend.manager.models.idle_checker.updaters import IdleCheckerUpdater


@dataclass(frozen=True)
class UpdateIdleCheckerAction(UpdateGlobalOpsAction[IdleCheckerRow, IdleCheckerData]):
    """Retune one stored idle checker definition."""

    updater: IdleCheckerUpdater

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return IDLE_CHECKER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_idle_checker"

    @override
    def to_updater(self) -> IdleCheckerUpdater:
        return self.updater
