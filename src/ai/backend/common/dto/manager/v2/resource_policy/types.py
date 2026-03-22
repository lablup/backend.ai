"""
Common types for Resource Policy DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.types import DefaultForUnspecified

__all__ = (
    "DefaultForUnspecified",
    "KeypairResourcePolicyOrderField",
    "OrderDirection",
    "ProjectResourcePolicyOrderField",
    "UserResourcePolicyOrderField",
)


class KeypairResourcePolicyOrderField(StrEnum):
    """Fields available for ordering keypair resource policies."""

    NAME = "name"
    CREATED_AT = "created_at"


class UserResourcePolicyOrderField(StrEnum):
    """Fields available for ordering user resource policies."""

    NAME = "name"
    CREATED_AT = "created_at"


class ProjectResourcePolicyOrderField(StrEnum):
    """Fields available for ordering project resource policies."""

    NAME = "name"
    CREATED_AT = "created_at"
