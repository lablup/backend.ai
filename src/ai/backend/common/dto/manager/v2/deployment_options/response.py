"""Response DTOs for deployment options sub-models."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.session_options import (
    HandlerOptionsEntryInfo,
    HandlerOptionsInfo,
)


class DeploymentHandlerOptionsInfo(BaseResponseModel):
    """Handler-keyed scheduler policy snapshot for deployments."""

    default: HandlerOptionsInfo = Field(
        description="Fallback per-handler policy.",
    )
    by_handler: list[HandlerOptionsEntryInfo] = Field(
        description="Per-handler overrides.",
    )


class DeploymentOptionsInfo(BaseResponseModel):
    """Per-deployment (or per-resource-group default) options payload."""

    handler_options: DeploymentHandlerOptionsInfo = Field(
        description="Handler-keyed scheduler policy (timeout + retry).",
    )
