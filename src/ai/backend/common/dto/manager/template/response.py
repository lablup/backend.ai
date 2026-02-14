"""
Response DTOs for template management system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    # Shared DTOs
    "SessionTemplateItemDTO",
    "SessionTemplateListItemDTO",
    "ClusterTemplateListItemDTO",
    "CreateSessionTemplateItemDTO",
    # Session template responses
    "CreateSessionTemplateResponse",
    "ListSessionTemplatesResponse",
    "GetSessionTemplateResponse",
    "UpdateSessionTemplateResponse",
    "DeleteSessionTemplateResponse",
    # Cluster template responses
    "CreateClusterTemplateResponse",
    "ListClusterTemplatesResponse",
    "GetClusterTemplateResponse",
    "UpdateClusterTemplateResponse",
    "DeleteClusterTemplateResponse",
)


# --- Shared DTOs ---


class SessionTemplateItemDTO(BaseModel):
    """Base DTO for a template item in list responses."""

    name: str = Field(description="Template name")
    id: str = Field(description="Template ID")
    created_at: str = Field(description="Creation timestamp")
    is_owner: bool = Field(description="Whether the current user is the owner")
    user: str | None = Field(description="Owner user UUID")
    group: str | None = Field(description="Group ID")
    user_email: str | None = Field(description="Owner user email")
    group_name: str | None = Field(description="Group name")


class SessionTemplateListItemDTO(SessionTemplateItemDTO):
    """Extended DTO for session template list including domain and template data."""

    domain_name: str = Field(description="Domain name")
    type: str = Field(description="Template type")
    template: dict[str, Any] = Field(description="Template data")


class ClusterTemplateListItemDTO(SessionTemplateItemDTO):
    """DTO for cluster template list items."""

    type: str = Field(description='Template type ("user" or "group")')


class CreateSessionTemplateItemDTO(BaseModel):
    """DTO for a single created session template entry."""

    id: str = Field(description="Created template ID")
    user: str = Field(description="Owner user UUID")


# --- Session Template Responses ---


class CreateSessionTemplateResponse(BaseResponseModel):
    """Response for creating session template(s)."""

    items: list[CreateSessionTemplateItemDTO] = Field(
        description="List of created session templates",
    )


class ListSessionTemplatesResponse(BaseResponseModel):
    """Response for listing session templates."""

    items: list[SessionTemplateListItemDTO] = Field(
        description="List of session templates",
    )


class GetSessionTemplateResponse(BaseResponseModel):
    """Response for getting a single session template."""

    template: dict[str, Any] = Field(description="Template data")
    name: str = Field(description="Template name")
    user_uuid: str = Field(description="Owner user UUID")
    group_id: str = Field(description="Group ID")
    domain_name: str = Field(description="Domain name")


class UpdateSessionTemplateResponse(BaseResponseModel):
    """Response for updating a session template."""

    success: bool = Field(description="Whether the update was successful")


class DeleteSessionTemplateResponse(BaseResponseModel):
    """Response for deleting a session template."""

    success: bool = Field(description="Whether the deletion was successful")


# --- Cluster Template Responses ---


class CreateClusterTemplateResponse(BaseResponseModel):
    """Response for creating a cluster template."""

    id: str = Field(description="Created template ID")
    user: str = Field(description="Owner user UUID")


class ListClusterTemplatesResponse(BaseResponseModel):
    """Response for listing cluster templates."""

    items: list[ClusterTemplateListItemDTO] = Field(
        description="List of cluster templates",
    )


class GetClusterTemplateResponse(BaseResponseModel):
    """Response for getting a single cluster template."""

    template: dict[str, Any] = Field(description="Template data")


class UpdateClusterTemplateResponse(BaseResponseModel):
    """Response for updating a cluster template."""

    success: bool = Field(description="Whether the update was successful")


class DeleteClusterTemplateResponse(BaseResponseModel):
    """Response for deleting a cluster template."""

    success: bool = Field(description="Whether the deletion was successful")
