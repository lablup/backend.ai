"""Request DTOs for the merged app_config v2 read."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "ResolveAppConfigInput",
    "ResolvePublicAppConfigInput",
)


class ResolveAppConfigInput(BaseRequestModel):
    """Input for resolving merged AppConfigs for the acting user.

    The scope is never caller-supplied: the adapter takes both the user and the domain from
    the session, so a resolve is only ever for the acting user in their own domain.
    """

    config_names: list[str] = Field(
        min_length=1, description="Config names to resolve the merged view for."
    )


class ResolvePublicAppConfigInput(BaseRequestModel):
    """Input for the anonymous, pre-login read, where only public fragments contribute.

    A pre-login screen usually needs several configs at once, so this takes the same batch
    as the authenticated resolve — it just names no principal.
    """

    config_names: list[str] = Field(
        min_length=1, description="Config names to resolve the merged public view for."
    )
