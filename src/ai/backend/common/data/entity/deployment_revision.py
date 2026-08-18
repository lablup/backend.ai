from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "DEPLOYMENT_REVISION_ENTITY_TYPE",
    "DeploymentRevisionID",
)


DEPLOYMENT_REVISION_ENTITY_TYPE = EntityType("deployment_revision")


class DeploymentRevisionID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_REVISION_ENTITY_TYPE
