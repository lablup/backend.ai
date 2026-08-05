"""Response DTOs for the merged app_config v2 read."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "AppConfigNode",
    "GetAppConfigsPayload",
)


class AppConfigNode(BaseResponseModel):
    """The merged AppConfig view for one config name."""

    config_name: str = Field(description="Added in 26.9.0. Config name this view is for.")
    config: dict[str, Any] = Field(
        description="Added in 26.9.0. Every fragment visible to the caller, deep-merged in "
        "ascending allow-list rank order. Empty when nothing visible contributes, or when "
        "everything that did was empty. Read the fragment API for the per-scope values behind it."
    )


class GetAppConfigsPayload(BaseResponseModel):
    """Payload for a merged AppConfig get."""

    app_configs: list[AppConfigNode] = Field(
        description="One merged view per requested config name, in request order; a repeated "
        "name is repeated here."
    )
