from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DEPLOYMENT_ENTITY_TYPE, DeploymentID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass
class ModelServiceAction(BaseSingleEntityAction):
    """Base for a legacy model service operation on one deployment.

    The routes, tokens, rules and errors a service carries are answered for by
    the deployment, so those operations carry its id.
    """

    deployment_id: DeploymentID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.deployment_id


@dataclass
class ModelServiceScopeAction(BaseScopeAction):
    """Base for a legacy model service operation bounded by a scope."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE


@dataclass
class ModelServiceScopeActionResult(BaseScopeActionResult):
    """A scoped model service read names no entity."""

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()
