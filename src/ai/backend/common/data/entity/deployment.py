"""Entity type, scope type and id of the deployments table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeType

__all__ = ("DeploymentEntityType", "DEPLOYMENT_SCOPE_TYPE", "DeploymentID")


class DeploymentEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "deployment"

    @override
    @classmethod
    def description(cls) -> str:
        return "A served model with its replicas and revisions."


DEPLOYMENT_SCOPE_TYPE = ScopeType(DeploymentEntityType())


class DeploymentID(EntityIdentifier):
    """A deployment's entity id."""

    @override
    def entity_type(self) -> EntityType:
        return DeploymentEntityType()
