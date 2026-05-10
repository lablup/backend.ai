from dataclasses import dataclass, field
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ModelRevisionData
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class ListActiveDeploymentsWithCurrentRevisionAction(DeploymentBaseAction):
    """Admin-only action that returns the current revision data for every
    active deployment.

    The adapter layer consumes the list, converts each
    ``ModelRevisionData`` into a ``ModelRevisionCreator``, and invokes the
    per-deployment refresh action.  The owning deployment is carried on
    ``ModelRevisionData.deployment_id`` so no wrapper type is needed.
    """

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class ListActiveDeploymentsWithCurrentRevisionActionResult(BaseActionResult):
    revisions: list[ModelRevisionData] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None
