"""Common permission types shared between manager and client."""

from __future__ import annotations

import enum


class RoleStatus(enum.StrEnum):
    """Status of a role."""

    ACTIVE = "active"
    # 'inactive' status is used when the role is temporarily disabled
    INACTIVE = "inactive"
    # 'deleted' status is used when the role is permanently removed
    DELETED = "deleted"


class RoleSource(enum.StrEnum):
    """Definition source of the role."""

    SYSTEM = "system"  # System-defined role, e.g., default roles
    CUSTOM = "custom"  # Custom role defined
