from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("DeploymentRevisionResourceSlotID",)


class DeploymentRevisionResourceSlotFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "deployment_revision_resource_slot"

    @override
    @classmethod
    def description(cls) -> str:
        return "One slot's amount a deployment revision declares."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return DeploymentEntityType


class DeploymentRevisionResourceSlotID(FieldIdentifier):
    """One slot's amount a deployment revision declares."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return DeploymentRevisionResourceSlotFieldType()
