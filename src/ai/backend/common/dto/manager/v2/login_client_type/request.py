"""Request DTOs for login_client_type v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel

__all__ = (
    "CreateLoginClientTypeInput",
    "UpdateLoginClientTypeInput",
)


class CreateLoginClientTypeInput(BaseRequestModel):
    """Input for creating a new login client type."""

    name: str = Field(
        min_length=1,
        max_length=64,
        description="Unique login client type name (e.g. 'core', 'webui').",
    )
    description: str | None = Field(
        default=None,
        description="Optional free-text description shown to administrators.",
    )


class UpdateLoginClientTypeInput(BaseRequestModel):
    """Input for updating a login client type.

    Fields default to "no change". For ``description``, pass ``null`` to clear the
    existing value; omit the field (SENTINEL) to leave it untouched.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="Updated name. Omit to leave unchanged.",
    )
    description: str | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated description. Use null to clear, omit to leave unchanged.",
    )
