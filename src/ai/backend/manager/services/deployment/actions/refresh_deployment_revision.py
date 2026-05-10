from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.creator import ModelRevisionCreator
from ai.backend.manager.data.deployment.types import RevisionRefreshResult
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class RefreshDeploymentRevisionAction(DeploymentBaseAction):
    """Admin-only action that adds and activates a fresh revision for a
    single deployment, given an already-prepared ``ModelRevisionCreator``.

    The adapter layer is responsible for projecting the previous revision's
    persisted ``ModelRevisionData`` onto a ``ModelRevisionCreator`` and
    passing it in here, so the service does not perform any type
    conversions.
    """

    deployment_id: DeploymentID
    creator: ModelRevisionCreator

    @override
    def entity_id(self) -> str | None:
        return str(self.deployment_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class RefreshDeploymentRevisionActionResult(BaseActionResult):
    result: RevisionRefreshResult

    @override
    def entity_id(self) -> str | None:
        return str(self.result.deployment_id)
