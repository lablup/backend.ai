"""Field type and id of the deployment_policies table."""

from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("DeploymentPolicyFieldType", "DeploymentPolicyID")


class DeploymentPolicyFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "deployment_policy"

    @override
    @classmethod
    def description(cls) -> str:
        return "How a deployment rolls out a new revision, rolling update or blue-green."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return DeploymentEntityType


class DeploymentPolicyID(FieldIdentifier):
    """A deployment policy's id.

    Each deployment has at most one policy row, read and written through the
    deployment that owns it.
    """

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return DeploymentPolicyFieldType()
