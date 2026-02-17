"""
Common DTOs for auto-scaling rule system used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import (
    AutoScalingRuleFilter,
    AutoScalingRuleOrder,
    CreateAutoScalingRuleRequest,
    DeleteAutoScalingRuleRequest,
    SearchAutoScalingRulesRequest,
    UpdateAutoScalingRuleRequest,
)
from .response import (
    AutoScalingRuleDTO,
    CreateAutoScalingRuleResponse,
    DeleteAutoScalingRuleResponse,
    GetAutoScalingRuleResponse,
    PaginationInfo,
    SearchAutoScalingRulesResponse,
    UpdateAutoScalingRuleResponse,
)
from .types import (
    AutoScalingRuleOrderField,
    OrderDirection,
)

__all__ = (
    # Types
    "OrderDirection",
    "AutoScalingRuleOrderField",
    # Request DTOs
    "CreateAutoScalingRuleRequest",
    "UpdateAutoScalingRuleRequest",
    "SearchAutoScalingRulesRequest",
    "DeleteAutoScalingRuleRequest",
    "AutoScalingRuleFilter",
    "AutoScalingRuleOrder",
    # Response DTOs
    "AutoScalingRuleDTO",
    "CreateAutoScalingRuleResponse",
    "GetAutoScalingRuleResponse",
    "SearchAutoScalingRulesResponse",
    "UpdateAutoScalingRuleResponse",
    "DeleteAutoScalingRuleResponse",
    "PaginationInfo",
)
