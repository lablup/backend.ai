"""Id of the endpoint tokens table."""

from typing import override

from ai.backend.common.data.entity.deployment import DEPLOYMENT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType, FieldIdentifier

__all__ = ("DeploymentTokenID",)


class DeploymentTokenID(FieldIdentifier):
    """An access token's id.

    A token grants access to one deployment and is authorized through it, so the
    deployment owns the row and the token declares no scope of its own.
    """

    @override
    @classmethod
    def owner_entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE
