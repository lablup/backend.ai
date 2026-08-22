from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DEPLOYMENT_ENTITY_TYPE, DeploymentID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass
class DeploymentSingleEntityAction(BaseSingleEntityAction):
    """Base for an operation on one deployment.

    Everything a deployment holds — its revisions, replicas, routes, tokens, rules
    and policy — is answered for by the deployment, so those operations carry its
    id rather than declaring a type of their own.
    """

    deployment_id: DeploymentID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.deployment_id


@dataclass
class DeploymentBaseAction(DeploymentSingleEntityAction):
    """Base for a deployment operation that names the deployment itself."""


@dataclass
class DeploymentGlobalAction(BaseGlobalAction):
    """Base for a deployment operation that names none."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE


@dataclass
class DeploymentScopeAction(BaseScopeAction):
    """Base for a deployment operation bounded by a scope."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE


@dataclass
class DeploymentScopeActionResult(BaseScopeActionResult):
    """A scoped deployment read names no entity."""

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()
