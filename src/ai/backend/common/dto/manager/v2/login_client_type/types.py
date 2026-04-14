"""Common types for login_client_type DTO v2."""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "LoginClientTypeOrderField",
    "OrderDirection",
)


class LoginClientTypeOrderField(StrEnum):
    """Fields available for ordering login client types."""

    NAME = "name"
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"
