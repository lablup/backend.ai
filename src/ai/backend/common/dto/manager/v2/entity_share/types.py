"""Shared enums of the entity share v2 API."""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "EntityShareOrderField",
    "EntityShareSideDTO",
    "EntityShareStatusDTO",
)


class EntityShareStatusDTO(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELED = "canceled"
    REVOKED = "revoked"


class EntityShareSideDTO(StrEnum):
    """Which side of a share the caller stands on."""

    RECIPIENT = "recipient"
    SHARER = "sharer"


class EntityShareOrderField(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    STATUS = "status"
