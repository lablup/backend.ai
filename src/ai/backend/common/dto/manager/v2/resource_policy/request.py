"""
Request DTOs for resource policy DTO v2.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel

from .types import DefaultForUnspecified

__all__ = (
    "CreateKeypairResourcePolicyInput",
    "CreateProjectResourcePolicyInput",
    "CreateUserResourcePolicyInput",
    "DeleteKeypairResourcePolicyInput",
    "DeleteProjectResourcePolicyInput",
    "DeleteUserResourcePolicyInput",
    "UpdateKeypairResourcePolicyInput",
    "UpdateProjectResourcePolicyInput",
    "UpdateUserResourcePolicyInput",
)


class CreateKeypairResourcePolicyInput(BaseRequestModel):
    """Input for creating a new keypair resource policy."""

    name: str = Field(
        min_length=1,
        max_length=256,
        description="Policy name. Must be non-empty after stripping whitespace.",
    )
    default_for_unspecified: DefaultForUnspecified = Field(
        description="Default resource allocation for unspecified resource slots.",
    )
    total_resource_slots: dict[str, Any] = Field(
        description="Total resource slot limits for sessions using this policy.",
    )
    max_session_lifetime: int = Field(
        description="Maximum lifetime of a session in seconds.",
    )
    max_concurrent_sessions: int = Field(
        description="Maximum number of concurrent sessions allowed.",
    )
    max_pending_session_count: int | None = Field(
        default=None,
        description="Maximum number of sessions in pending state. Null means unlimited.",
    )
    max_pending_session_resource_slots: dict[str, Any] | None = Field(
        default=None,
        description="Maximum resource slots occupied by pending sessions. Null means unlimited.",
    )
    max_concurrent_sftp_sessions: int = Field(
        description="Maximum number of concurrent SFTP sessions allowed.",
    )
    max_containers_per_session: int = Field(
        description="Maximum number of containers allowed per session.",
    )
    idle_timeout: int = Field(
        description="Idle timeout for sessions in seconds.",
    )
    allowed_vfolder_hosts: dict[str, Any] = Field(
        description="Allowed vfolder host permissions for this policy.",
    )

    @field_validator("name", mode="before")
    @classmethod
    def strip_and_validate_name(cls, v: str) -> str:
        """Strip whitespace and ensure name is non-blank."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank after stripping whitespace")
        return stripped


class UpdateKeypairResourcePolicyInput(BaseRequestModel):
    """Input for updating a keypair resource policy. All fields optional for partial update."""

    default_for_unspecified: DefaultForUnspecified | None = Field(
        default=None,
        description="Updated default resource allocation. Leave null to keep existing value.",
    )
    total_resource_slots: dict[str, Any] | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated resource slot limits. Use SENTINEL to clear, null to keep existing.",
    )
    max_session_lifetime: int | None = Field(
        default=None,
        description="Updated maximum session lifetime in seconds. Leave null to keep existing.",
    )
    max_concurrent_sessions: int | None = Field(
        default=None,
        description="Updated maximum concurrent sessions. Leave null to keep existing.",
    )
    max_pending_session_count: int | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated max pending sessions. Use SENTINEL to clear, null to keep existing.",
    )
    max_pending_session_resource_slots: dict[str, Any] | Sentinel | None = Field(
        default=SENTINEL,
        description=(
            "Updated max pending session resource slots. "
            "Use SENTINEL to clear, null to keep existing."
        ),
    )
    max_concurrent_sftp_sessions: int | None = Field(
        default=None,
        description="Updated max concurrent SFTP sessions. Leave null to keep existing.",
    )
    max_containers_per_session: int | None = Field(
        default=None,
        description="Updated max containers per session. Leave null to keep existing.",
    )
    idle_timeout: int | None = Field(
        default=None,
        description="Updated idle timeout in seconds. Leave null to keep existing.",
    )
    allowed_vfolder_hosts: dict[str, Any] | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated vfolder host permissions. Use SENTINEL to clear, null to keep existing.",
    )


class DeleteKeypairResourcePolicyInput(BaseRequestModel):
    """Input for deleting a keypair resource policy."""

    name: str = Field(description="Name of the keypair resource policy to delete.")


class CreateUserResourcePolicyInput(BaseRequestModel):
    """Input for creating a new user resource policy."""

    name: str = Field(
        min_length=1,
        max_length=256,
        description="Policy name. Must be non-empty after stripping whitespace.",
    )
    max_vfolder_count: int = Field(
        description="Maximum number of vfolders a user can create.",
    )
    max_quota_scope_size: int = Field(
        description="Maximum quota scope size in bytes.",
    )
    max_session_count_per_model_session: int = Field(
        description="Maximum number of sessions allowed per model session.",
    )
    max_customized_image_count: int = Field(
        description="Maximum number of customized images a user can create.",
    )

    @field_validator("name", mode="before")
    @classmethod
    def strip_and_validate_name(cls, v: str) -> str:
        """Strip whitespace and ensure name is non-blank."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank after stripping whitespace")
        return stripped


class UpdateUserResourcePolicyInput(BaseRequestModel):
    """Input for updating a user resource policy. All fields optional for partial update."""

    max_vfolder_count: int | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated max vfolder count. Use SENTINEL to clear, null to keep existing.",
    )
    max_quota_scope_size: int | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated max quota scope size. Use SENTINEL to clear, null to keep existing.",
    )
    max_session_count_per_model_session: int | None = Field(
        default=None,
        description="Updated max sessions per model session. Leave null to keep existing.",
    )
    max_customized_image_count: int | None = Field(
        default=None,
        description="Updated max customized image count. Leave null to keep existing.",
    )


class DeleteUserResourcePolicyInput(BaseRequestModel):
    """Input for deleting a user resource policy."""

    name: str = Field(description="Name of the user resource policy to delete.")


class CreateProjectResourcePolicyInput(BaseRequestModel):
    """Input for creating a new project resource policy."""

    name: str = Field(
        min_length=1,
        max_length=256,
        description="Policy name. Must be non-empty after stripping whitespace.",
    )
    max_vfolder_count: int = Field(
        description="Maximum number of vfolders a project can have.",
    )
    max_quota_scope_size: int = Field(
        description="Maximum quota scope size in bytes.",
    )
    max_network_count: int = Field(
        description="Maximum number of networks a project can create.",
    )

    @field_validator("name", mode="before")
    @classmethod
    def strip_and_validate_name(cls, v: str) -> str:
        """Strip whitespace and ensure name is non-blank."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank after stripping whitespace")
        return stripped


class UpdateProjectResourcePolicyInput(BaseRequestModel):
    """Input for updating a project resource policy. All fields optional for partial update."""

    max_vfolder_count: int | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated max vfolder count. Use SENTINEL to clear, null to keep existing.",
    )
    max_quota_scope_size: int | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated max quota scope size. Use SENTINEL to clear, null to keep existing.",
    )
    max_network_count: int | None = Field(
        default=None,
        description="Updated max network count. Leave null to keep existing.",
    )


class DeleteProjectResourcePolicyInput(BaseRequestModel):
    """Input for deleting a project resource policy."""

    name: str = Field(description="Name of the project resource policy to delete.")
