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
        description="Deep-merged config in ascending allow-list rank order. At least one fragment "
        "always contributes (a name nothing contributes to fails the call with a 404), so this is "
        "never null; an empty object means the contributing fragments were themselves empty."
    )
    fragments: list[AppConfigFragmentNode] = Field(
        description="The fragments that contributed to the merge, in ascending allow-list rank order."
    )


class GetAppConfigsPayload(BaseResponseModel):
    """Payload for a merged AppConfig get."""

    app_configs: list[AppConfigNode] = Field(
        description="One merged view per requested config name, in request order; a repeated "
        "name is repeated here."
    )
