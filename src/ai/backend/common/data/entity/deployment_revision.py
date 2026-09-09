from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = (
    "DeploymentRevisionFieldType",
    "DeploymentRevisionID",
)


class DeploymentRevisionFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "deployment_revision"

    @override
    @classmethod
    def description(cls) -> str:
        return "One configuration a deployment has run with."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return DeploymentEntityType


class DeploymentRevisionID(FieldIdentifier):
    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return DeploymentRevisionFieldType()
