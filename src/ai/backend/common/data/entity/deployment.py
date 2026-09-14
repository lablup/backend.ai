"""Entity type and id of the deployments table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("DeploymentEntityType", "DeploymentID")


class DeploymentEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "deployment"

    @override
    @classmethod
    def description(cls) -> str:
        return "A model service holding the replica count to keep and the replica group serving it."


class DeploymentID(EntityIdentifier):
    """A deployment's entity id."""

    @override
    def entity_type(self) -> EntityType:
        return DeploymentEntityType()
