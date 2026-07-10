"""Response DTOs for the merged app_config v2 read."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.app_config_fragment.response import AppConfigFragmentNode

__all__ = (
    "AppConfigNode",
    "ResolveAppConfigPayload",
)


class AppConfigNode(BaseResponseModel):
    """The merged AppConfig view for one config name."""

    config_name: str = Field(description="Config name this merged view is for.")
    merged_config: dict[str, Any] | None = Field(
        description="Deep-merged config in ascending allow-list rank order; null when no fragment "
        "contributes (the config name is defined but unconfigured for this scope)."
    )
    fragments: list[AppConfigFragmentNode] = Field(
        description="The fragments that contributed to the merge, in ascending allow-list rank order."
    )


class ResolveAppConfigPayload(BaseResponseModel):
    """Payload for a merged AppConfig resolve."""

    app_config: AppConfigNode = Field(description="The merged AppConfig view.")
