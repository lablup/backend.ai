"""Request DTOs for the merged app_config v2 read."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = ("ResolveAppConfigInput",)


class ResolveAppConfigInput(BaseRequestModel):
    """Input for resolving the merged AppConfig for one ``(user, config_name)``.

    ``user_id`` must match the authenticated caller (enforced by the adapter until an RBAC
    validator is in place).
    """

    config_name: str = Field(
        min_length=1, max_length=128, description="Config name to resolve the merged view for."
    )
    domain_id: UUID = Field(description="The resolving user's domain id.")
    user_id: UUID = Field(description="The resolving user's id (must be the caller).")
