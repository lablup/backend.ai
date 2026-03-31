from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.runtime_variant.actions.base import RuntimeVariantAction


@dataclass
class UpdateRuntimeVariantAction(RuntimeVariantAction):
    id: UUID
    updater: Updater[RuntimeVariantRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateRuntimeVariantActionResult(BaseActionResult):
    runtime_variant: RuntimeVariantData

    @override
    def entity_id(self) -> str | None:
        return str(self.runtime_variant.id)
