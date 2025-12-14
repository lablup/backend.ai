"""
Data types for domain service.
Deprecated: use `ai.backend.manager.data.domain.types` instead.
"""

from ai.backend.manager.data.domain.types import (
    DomainData,
    DomainModifier,
    DomainNodeModifier,
    UserInfo,
)
from ai.backend.manager.types import OptionalState, PartialModifier, TriState

__all__ = [
    "DomainData",
    "DomainModifier",
    "DomainNodeModifier",
    "UserInfo",
    "OptionalState",
    "PartialModifier",
    "TriState",
]
