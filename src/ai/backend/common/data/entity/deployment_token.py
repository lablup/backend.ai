"""Id of the endpoint tokens table."""

from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("DeploymentTokenID",)


DEPLOYMENT_TOKEN_FIELD_TYPE = FieldType("deployment_token")


class DeploymentTokenID(FieldIdentifier):
    """An access token's id.

    A token grants access to one deployment and is authorized through it, so the
    deployment owns the row and the token declares no scope of its own.
    """

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return DEPLOYMENT_TOKEN_FIELD_TYPE
