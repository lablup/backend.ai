"""
Path parameter DTOs for group REST API endpoints.
"""

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class GetGroupPathParam(BaseRequestModel):
    """Path parameter for getting a group."""

    group_id: UUID = Field(description="The group ID to retrieve")


class UpdateGroupPathParam(BaseRequestModel):
    """Path parameter for updating a group."""

    group_id: UUID = Field(description="The group ID to update")


class DeleteGroupPathParam(BaseRequestModel):
    """Path parameter for deleting a group."""

    group_id: UUID = Field(description="The group ID to delete")


class GroupMembersPathParam(BaseRequestModel):
    """Path parameter for group member operations."""

    group_id: UUID = Field(description="The group ID for member operations")
