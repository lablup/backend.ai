"""Request DTOs for deployment options sub-models."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.session_options import (
    HandlerOptionsEntryInput,
    HandlerOptionsInput,
)


class DeploymentHandlerOptionsInput(BaseRequestModel):
    """Handler-keyed scheduler policy for deployments.

    ``default`` is the fallback applied to any handler not listed in
    ``by_handler``; field-level ``null`` within either layer means
    "fall back to global defaults" (unbounded timeout, global retry
    fallback).
    """

    default: HandlerOptionsInput = Field(
        default_factory=HandlerOptionsInput,
        description="Fallback per-handler policy.",
    )
    by_handler: list[HandlerOptionsEntryInput] = Field(
        default_factory=list,
        description=(
            "Per-handler overrides. Duplicate handler_name entries are rejected by the server."
        ),
    )


class DeploymentOptionsInput(BaseRequestModel):
    """Per-deployment (or per-resource-group default) options payload."""

    handler_options: DeploymentHandlerOptionsInput = Field(
        description="Handler-keyed scheduler policy (timeout + retry).",
    )
