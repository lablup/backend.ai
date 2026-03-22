"""
Request DTOs for resource group DTO v2.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel

__all__ = (
    "CreateResourceGroupInput",
    "UpdateResourceGroupInput",
    "DeleteResourceGroupInput",
)


class CreateResourceGroupInput(BaseRequestModel):
    """Input for creating a new resource group."""

    name: str = Field(
        min_length=1,
        max_length=256,
        description="Resource group name. Must be non-empty after stripping whitespace.",
    )
    domain_name: str = Field(
        description="Domain name the resource group belongs to.",
    )
    description: str | None = Field(
        default=None,
        description="Human-readable description of the resource group.",
    )
    total_resource_slots: dict[str, Any] | None = Field(
        default=None,
        description="Total resource slot limits for the resource group.",
    )
    allowed_vfolder_hosts: dict[str, Any] | None = Field(
        default=None,
        description="Allowed vfolder host permissions for the resource group.",
    )
    integration_id: str | None = Field(
        default=None,
        description="External integration ID associated with this resource group.",
    )
    resource_policy: str | None = Field(
        default=None,
        description="Resource policy name to apply to this resource group.",
    )

    @field_validator("name", mode="before")
    @classmethod
    def strip_and_validate_name(cls, v: str) -> str:
        """Strip whitespace and ensure name is non-blank."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank after stripping whitespace")
        return stripped


class UpdateResourceGroupInput(BaseRequestModel):
    """Input for updating a resource group. All fields optional for partial update."""

    name: str | None = Field(
        default=None,
        description="Updated resource group name. Leave null to keep existing value.",
    )
    description: str | Sentinel | None = Field(
        default=SENTINEL,
        description=("Updated description. Use SENTINEL to clear, null to keep existing value."),
    )
    is_active: bool | None = Field(
        default=None,
        description="Whether the resource group is active. Leave null to keep existing value.",
    )
    total_resource_slots: dict[str, Any] | Sentinel | None = Field(
        default=SENTINEL,
        description=(
            "Updated total resource slot limits. Use SENTINEL to clear, null to keep existing value."
        ),
    )
    allowed_vfolder_hosts: dict[str, Any] | Sentinel | None = Field(
        default=SENTINEL,
        description=(
            "Updated allowed vfolder host permissions. "
            "Use SENTINEL to clear, null to keep existing value."
        ),
    )
    integration_id: str | Sentinel | None = Field(
        default=SENTINEL,
        description=(
            "Updated external integration ID. Use SENTINEL to clear, null to keep existing value."
        ),
    )
    resource_policy: str | Sentinel | None = Field(
        default=SENTINEL,
        description=(
            "Updated resource policy name. Use SENTINEL to clear, null to keep existing value."
        ),
    )


class DeleteResourceGroupInput(BaseRequestModel):
    """Input for deleting a resource group."""

    id: UUID = Field(
        description="UUID of the resource group to delete.",
    )
