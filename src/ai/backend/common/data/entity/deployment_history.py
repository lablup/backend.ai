"""Field type and id of the deployment history table."""

from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("DEPLOYMENT_HISTORY_FIELD_TYPE", "DeploymentHistoryID")

DEPLOYMENT_HISTORY_FIELD_TYPE = FieldType("deployment_history")


class DeploymentHistoryID(FieldIdentifier):
    """A deployment history row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return DEPLOYMENT_HISTORY_FIELD_TYPE
