"""
Resource slot DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.resource_slot.response import (
    ResourceSlotTypeNode,
)
from ai.backend.common.dto.manager.v2.resource_slot.types import (
    NumberFormatInfo,
    OrderDirection,
    ResourceSlotTypeOrderField,
)

__all__ = (
    # Types
    "NumberFormatInfo",
    "OrderDirection",
    "ResourceSlotTypeOrderField",
    # Node models (response)
    "ResourceSlotTypeNode",
)
