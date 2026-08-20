"""Entity type, scope type and id of the deployments table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeType

__all__ = ("DEPLOYMENT_ENTITY_TYPE", "DEPLOYMENT_SCOPE_TYPE", "DeploymentID")

DEPLOYMENT_ENTITY_TYPE = EntityType("deployment")
DEPLOYMENT_SCOPE_TYPE = ScopeType(DEPLOYMENT_ENTITY_TYPE)


class DeploymentID(EntityIdentifier):
    """A deployment's entity id."""

    @override
    def entity_type(self) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE
