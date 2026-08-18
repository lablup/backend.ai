from typing import override

from ai.backend.common.data.entity.deployment_revision import DEPLOYMENT_REVISION_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType, FieldIdentifier

__all__ = ("DeploymentRevisionResourceSlotID",)


class DeploymentRevisionResourceSlotID(FieldIdentifier):
    """One slot's amount a deployment revision declares."""

    @override
    @classmethod
    def owner_entity_type(cls) -> EntityType:
        return DEPLOYMENT_REVISION_ENTITY_TYPE
