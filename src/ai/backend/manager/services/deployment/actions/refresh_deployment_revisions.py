from dataclasses import dataclass, field
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import RevisionRefreshResult
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class RefreshDeploymentRevisionsAction(DeploymentBaseAction):
    """Admin-only action to refresh revisions for all active deployments.

    Creates a new revision based on each active deployment's current revision
    and activates it, allowing DeploymentController to re-resolve preset,
    deployment-config, and model_definition.
    """

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class RefreshDeploymentRevisionsActionResult(BaseActionResult):
    results: list[RevisionRefreshResult] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None
