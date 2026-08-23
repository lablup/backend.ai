"""Field type and id of the deployment_policies table."""

from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("DEPLOYMENT_POLICY_FIELD_TYPE", "DeploymentPolicyID")

DEPLOYMENT_POLICY_FIELD_TYPE = FieldType("deployment_policy")


class DeploymentPolicyID(FieldIdentifier):
    """A deployment policy's id.

    Each deployment has at most one policy row, read and written through the
    deployment that owns it.
    """

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return DEPLOYMENT_POLICY_FIELD_TYPE
