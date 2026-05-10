from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.creator import ModelRevisionCreator
from ai.backend.manager.data.deployment.types import RevisionRefreshResult
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class RefreshDeploymentRevisionsAction(DeploymentBaseAction):
    """Admin-only batch action that adds and activates a fresh revision for
    each deployment in ``creators_by_id``.

    The adapter layer is responsible for projecting each previous-revision
    ``ModelRevisionData`` onto a ``ModelRevisionCreator`` before invoking
    this action; the service does no type conversion of its own. Each
    deployment is processed independently so a single failure does not
    abort the rest (partial success by design).
    """

    creators_by_id: Mapping[DeploymentID, ModelRevisionCreator]

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
