"""Request DTOs for resource allocation v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "AdminEffectiveResourceAllocationInput",
    "CheckPresetAvailabilityInput",
    "EffectiveResourceAllocationInput",
)


class EffectiveResourceAllocationInput(BaseRequestModel):
    """Input for querying effective assignable resources for the current user."""

    project_id: UUID = Field(description="Project ID to check allocation for.")
    resource_group_name: str = Field(description="Resource group name to check allocation for.")


class AdminEffectiveResourceAllocationInput(BaseRequestModel):
    """Input for admin querying effective assignable resources for a specific user."""

    user_id: UUID = Field(description="Target user ID.")
    project_id: UUID = Field(description="Project ID to check allocation for.")
    resource_group_name: str = Field(description="Resource group name to check allocation for.")


class CheckPresetAvailabilityInput(BaseRequestModel):
    """Input for checking which resource presets are available."""

    project_id: UUID = Field(description="Project ID to check availability for.")
    resource_group_name: str = Field(description="Resource group name to check availability for.")
