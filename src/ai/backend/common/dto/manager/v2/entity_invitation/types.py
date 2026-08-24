"""Shared enums of the entity invitation v2 API."""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "EntityInvitationOrderField",
    "EntityInvitationSideDTO",
    "EntityInvitationStatusDTO",
)


class EntityInvitationStatusDTO(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELED = "canceled"


class EntityInvitationOrderField(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    STATUS = "status"


class EntityInvitationSideDTO(StrEnum):
    """Which side of an invitation a read comes in through."""

    RECEIVED = "received"
    SENT = "sent"
    TARGET = "target"
