from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("DeploymentRevisionResourceSlotID",)


DEPLOYMENT_REVISION_RESOURCE_SLOT_FIELD_TYPE = FieldType("deployment_revision_resource_slot")


class DeploymentRevisionResourceSlotID(FieldIdentifier):
    """One slot's amount a deployment revision declares."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return DEPLOYMENT_REVISION_RESOURCE_SLOT_FIELD_TYPE
