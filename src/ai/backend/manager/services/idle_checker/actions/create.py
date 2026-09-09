from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.idle_checker import IdleCheckerEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalOpsAction
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.models.idle_checker.creators import IdleCheckerCreator
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow


@dataclass(frozen=True)
class CreateIdleCheckerAction(CreateGlobalOpsAction[IdleCheckerRow, IdleCheckerData]):
    """Add an idle checker definition to the global catalog."""

    creator: IdleCheckerCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return IdleCheckerEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_idle_checker"

    @override
    def to_creator(self) -> IdleCheckerCreator:
        return self.creator
