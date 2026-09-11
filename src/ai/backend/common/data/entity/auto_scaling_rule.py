"""Type and id of the endpoint_auto_scaling_rules table, a field row of a deployment."""

from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.types import EntityType, FieldIdentifier, FieldType

__all__ = ("AutoScalingRuleFieldType", "AutoScalingRuleID")


class AutoScalingRuleFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "auto_scaling_rule"

    @override
    @classmethod
    def description(cls) -> str:
        return "One rule scaling a deployment's replica count by a metric."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return DeploymentEntityType


class AutoScalingRuleID(FieldIdentifier):
    """An auto-scaling rule row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return AutoScalingRuleFieldType()
