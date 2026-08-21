"""
Data types for group service.
Deprecated: use `ai.backend.manager.data.project.types` instead.
"""

from ai.backend.manager.data.project.types import (
    ProjectData,
    ProjectModifier,
    ProjectType,
)
from ai.backend.manager.types import OptionalState, PartialModifier, TriState

__all__ = [
    "ProjectData",
    "ProjectModifier",
    "OptionalState",
    "PartialModifier",
    "ProjectType",
    "TriState",
]
