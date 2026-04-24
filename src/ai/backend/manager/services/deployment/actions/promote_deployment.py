"""Action for manually promoting a blue-green deployment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class PromoteDeploymentAction(DeploymentBaseAction):
    """Action to manually promote a blue-green deployment.

    Triggers immediate traffic switch from blue (old) to green (new) routes
    when the deployment is in AWAITING_PROMOTION state.
    """

    deployment_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.deployment_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class PromoteDeploymentActionResult(BaseActionResult):
    """Result of promoting a deployment."""

    deployment: ModelDeploymentData

    @override
    def entity_id(self) -> str | None:
        return str(self.deployment.id)
