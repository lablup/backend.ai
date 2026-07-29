"""Request DTOs for the merged app_config v2 read."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "MyGetAppConfigsInput",
    "PublicGetAppConfigsInput",
)


class MyGetAppConfigsInput(BaseRequestModel):
    """Input for the acting user's merged AppConfigs; the scope comes from the session."""

    config_names: list[str] = Field(
        min_length=1, description="Config names to get the merged view for."
    )


class PublicGetAppConfigsInput(BaseRequestModel):
    """Input for the anonymous, pre-login read, where only public fragments contribute."""

    config_names: list[str] = Field(
        min_length=1, description="Config names to get the merged public view for."
    )
