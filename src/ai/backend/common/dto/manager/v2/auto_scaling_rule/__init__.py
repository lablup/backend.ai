"""
Auto-scaling rule DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.auto_scaling_rule.request import (
    AutoScalingRuleFilter,
    AutoScalingRuleOrder,
    CreateAutoScalingRuleInput,
    DeleteAutoScalingRuleInput,
    SearchAutoScalingRulesInput,
    UpdateAutoScalingRuleInput,
)
from ai.backend.common.dto.manager.v2.auto_scaling_rule.response import (
    AutoScalingRuleNode,
    CreateAutoScalingRulePayload,
    DeleteAutoScalingRulePayload,
    GetAutoScalingRulePayload,
    SearchAutoScalingRulesPayload,
    UpdateAutoScalingRulePayload,
)
from ai.backend.common.dto.manager.v2.auto_scaling_rule.types import (
    AutoScalingMetricSource,
    AutoScalingRuleOrderField,
    OrderDirection,
)

__all__ = (
    # Types
    "AutoScalingMetricSource",
    "AutoScalingRuleOrderField",
    "OrderDirection",
    # Input models (request)
    "AutoScalingRuleFilter",
    "AutoScalingRuleOrder",
    "CreateAutoScalingRuleInput",
    "DeleteAutoScalingRuleInput",
    "SearchAutoScalingRulesInput",
    "UpdateAutoScalingRuleInput",
    # Response models
    "AutoScalingRuleNode",
    "CreateAutoScalingRulePayload",
    "DeleteAutoScalingRulePayload",
    "GetAutoScalingRulePayload",
    "SearchAutoScalingRulesPayload",
    "UpdateAutoScalingRulePayload",
)
