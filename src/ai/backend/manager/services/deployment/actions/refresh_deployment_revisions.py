from dataclasses import dataclass, field
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import RevisionRefreshResult
from ai.backend.manager.services.deployment.actions.base import DeploymentGlobalAction


@dataclass
class GlobalRefreshDeploymentRevisionsAction(DeploymentGlobalAction):
    """Admin-only action to refresh revisions for all active deployments.

    Creates a new revision based on each active deployment's current revision
    and activates it, allowing DeploymentController to re-resolve preset,
    deployment-config, and model_definition.
    """

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_refresh_deployment_revisions"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class GlobalRefreshDeploymentRevisionsActionResult:
    results: list[RevisionRefreshResult] = field(default_factory=list)
