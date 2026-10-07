"""Response DTOs for deployment options sub-models."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel


class HandlerOptionsInfo(BaseResponseModel):
    """Per-handler scheduler policy snapshot for deployments."""

    timeout_sec: int | None = Field(
        description="Phase timeout in seconds; `null` means unbounded for this entry.",
    )
    max_retry_count: int | None = Field(
        description=(
            "Per-phase retry budget; `null` means the retry limit is "
            "disabled (`give_up` never fires for this handler)."
        ),
    )


class HandlerOptionsEntryInfo(HandlerOptionsInfo):
    """A named deployment handler's scheduler policy snapshot."""

    handler_name: str = Field(
        description="Handler identifier matching `SessionLifecycleHandler.name()`."
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
