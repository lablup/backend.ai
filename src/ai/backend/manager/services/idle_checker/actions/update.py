from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow
from ai.backend.manager.repositories.base import Updater
from ai.backend.manager.services.idle_checker.actions.base import IdleCheckerGlobalAction


@dataclass(frozen=True)
class UpdateIdleCheckerAction(IdleCheckerGlobalAction):
    updater: Updater[IdleCheckerRow]

    @override
    def entity_id(self) -> str:
        return str(self.updater.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass(frozen=True)
class UpdateIdleCheckerActionResult(BaseActionResult):
    idle_checker: IdleCheckerData

    @override
    def entity_id(self) -> str:
        return str(self.idle_checker.id)
