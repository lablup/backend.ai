"""
Request DTOs for template management system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from pydantic import AliasChoices, Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    # Path params
    "TemplatePathParam",
    # Session template requests
    "CreateSessionTemplateRequest",
    "ListSessionTemplatesRequest",
    "GetSessionTemplateRequest",
    "UpdateSessionTemplateRequest",
    "DeleteSessionTemplateRequest",
    # Cluster template requests
    "CreateClusterTemplateRequest",
    "ListClusterTemplatesRequest",
    "GetClusterTemplateRequest",
    "UpdateClusterTemplateRequest",
    "DeleteClusterTemplateRequest",
)


class TemplatePathParam(BaseRequestModel):
    """Path parameter for template endpoints."""

    template_id: str = Field(description="Template ID from URL path")


# --- Session Template Requests ---


class CreateSessionTemplateRequest(BaseRequestModel):
    """Request body for creating a session template."""

    group: str = Field(
        default="default",
        validation_alias=AliasChoices("group", "groupName", "group_name"),
        description="Group name",
    )
    domain: str = Field(
        default="default",
        validation_alias=AliasChoices("domain", "domainName", "domain_name"),
        description="Domain name",
    )
    owner_access_key: str | None = Field(
        default=None,
        description="Access key of the owner (for admin use)",
    )
    payload: str = Field(description="JSON or YAML string containing template definition")


class ListSessionTemplatesRequest(BaseRequestModel):
    """Request parameters for listing session templates."""

    all: bool = Field(
        default=False,
        description="List all templates (superadmin only)",
    )
    group_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("group_id", "groupId"),
        description="Filter by group ID",
    )


class GetSessionTemplateRequest(BaseRequestModel):
    """Request parameters for getting a session template."""

    format: str = Field(
        default="json",
        description='Response format: "yaml" or "json"',
    )
    owner_access_key: str | None = Field(
        default=None,
        description="Access key of the owner (for admin use)",
    )


class UpdateSessionTemplateRequest(BaseRequestModel):
    """Request body for updating a session template."""

    group: str = Field(
        default="default",
        validation_alias=AliasChoices("group", "groupName", "group_name"),
        description="Group name",
    )
    domain: str = Field(
        default="default",
        validation_alias=AliasChoices("domain", "domainName", "domain_name"),
        description="Domain name",
    )
    payload: str = Field(description="JSON or YAML string containing template definition")
    owner_access_key: str | None = Field(
        default=None,
        description="Access key of the owner (for admin use)",
    )


class DeleteSessionTemplateRequest(BaseRequestModel):
    """Request parameters for deleting a session template."""

    owner_access_key: str | None = Field(
        default=None,
        description="Access key of the owner (for admin use)",
    )


# --- Cluster Template Requests ---


class CreateClusterTemplateRequest(BaseRequestModel):
    """Request body for creating a cluster template."""

    group: str = Field(
        default="default",
        validation_alias=AliasChoices("group", "groupName", "group_name"),
        description="Group name",
    )
    domain: str = Field(
        default="default",
        validation_alias=AliasChoices("domain", "domainName", "domain_name"),
        description="Domain name",
    )
    owner_access_key: str | None = Field(
        default=None,
        description="Access key of the owner (for admin use)",
    )
    payload: str = Field(description="JSON or YAML string containing cluster template definition")


class ListClusterTemplatesRequest(BaseRequestModel):
    """Request parameters for listing cluster templates."""

    all: bool = Field(
        default=False,
        description="List all templates (superadmin only)",
    )
    group_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("group_id", "groupId"),
        description="Filter by group ID",
    )


class GetClusterTemplateRequest(BaseRequestModel):
    """Request parameters for getting a cluster template."""

    format: str = Field(
        default="yaml",
        description='Response format: "yaml" or "json"',
    )
    owner_access_key: str | None = Field(
        default=None,
        description="Access key of the owner (for admin use)",
    )


class UpdateClusterTemplateRequest(BaseRequestModel):
    """Request body for updating a cluster template."""

    payload: str = Field(description="JSON or YAML string containing cluster template definition")
    owner_access_key: str | None = Field(
        default=None,
        description="Access key of the owner (for admin use)",
    )


class DeleteClusterTemplateRequest(BaseRequestModel):
    """Request parameters for deleting a cluster template."""

    owner_access_key: str | None = Field(
        default=None,
        description="Access key of the owner (for admin use)",
    )
