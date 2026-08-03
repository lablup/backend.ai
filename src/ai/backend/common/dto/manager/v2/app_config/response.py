"""Response DTOs for the merged app_config v2 read."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.app_config_fragment.response import AppConfigFragmentNode

__all__ = (
    "AppConfigNode",
    "GetAppConfigsPayload",
)


class AppConfigNode(BaseResponseModel):
    """The merged AppConfig view for one config name."""

    config_name: str = Field(description="Config name this merged view is for.")
    merged_config: dict[str, Any] = Field(
        description="Deep-merged config in ascending allow-list rank order. Empty when nothing "
        "visible to the caller contributes, or when every contributing fragment was empty."
    )
    fragments: list[AppConfigFragmentNode] = Field(
        description="The fragments that contributed, in ascending allow-list rank order."
    )


class GetAppConfigsPayload(BaseResponseModel):
    """Payload for a merged AppConfig get."""

    app_configs: list[AppConfigNode] = Field(
        description="One merged view per requested config name, in request order; a repeated "
        "name is repeated here."
    )
