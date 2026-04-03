from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.model_card.actions.base import ModelCardAction


@dataclass
class DeployModelCardAction(ModelCardAction):
    """Deploy a model card by creating a deployment with a revision preset."""

    model_card_id: UUID
    revision_preset_id: UUID
    resource_group: str
    desired_replica_count: int = 1
    requester_id: UUID | None = None

    @override
    def entity_id(self) -> str | None:
        return str(self.model_card_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class DeployModelCardActionResult(BaseActionResult):
    deployment_id: UUID
    deployment_name: str

    @override
    def entity_id(self) -> str | None:
        return str(self.deployment_id)
