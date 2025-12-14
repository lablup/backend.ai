"""
Data types for group service.
Deprecated: use `ai.backend.manager.data.group.types` instead.
"""

from ai.backend.manager.data.group.types import (
    GroupCreator,
    GroupData,
    GroupModifier,
    ProjectType,
)
from ai.backend.manager.types import OptionalState, PartialModifier, TriState

__all__ = [
    "GroupCreator",
    "GroupData",
    "GroupModifier",
    "ProjectType",
    "OptionalState",
    "PartialModifier",
    "TriState",
]
