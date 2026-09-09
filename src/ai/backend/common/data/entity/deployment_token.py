"""Id of the endpoint tokens table."""

from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("DeploymentTokenFieldType", "DeploymentTokenID")


class DeploymentTokenFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "deployment_token"

    @override
    @classmethod
    def description(cls) -> str:
        return "An access token issued for a deployment."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return DeploymentEntityType


class DeploymentTokenID(FieldIdentifier):
    """An access token's id.

    A token grants access to one deployment and is authorized through it, so the
    deployment owns the row and the token declares no scope of its own.
    """

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return DeploymentTokenFieldType()
