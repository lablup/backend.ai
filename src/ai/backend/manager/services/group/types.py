"""
Data types for group service.
Deprecated: use `ai.backend.manager.data.group.types` instead.
"""

from ai.backend.manager.data.group.types import (
    GroupData,
    GroupModifier,
    ProjectType,
)
from ai.backend.manager.types import OptionalState, PartialModifier, TriState

__all__ = [
    "GroupData",
    "GroupModifier",
    "ProjectType",
    "OptionalState",
    "PartialModifier",
    "TriState",
]
