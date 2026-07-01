"""
Types for role invitation DTOs v2.
"""

from __future__ import annotations

from enum import StrEnum


class RoleInvitationStateDTO(StrEnum):
    """Role invitation state."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELED = "canceled"
