from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = (
    "DEPLOYMENT_REVISION_FIELD_TYPE",
    "DeploymentRevisionID",
)


DEPLOYMENT_REVISION_FIELD_TYPE = FieldType("deployment_revision")


class DeploymentRevisionID(FieldIdentifier):
    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return DEPLOYMENT_REVISION_FIELD_TYPE
