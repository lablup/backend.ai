"""
Request DTOs for Deployment DTO v2.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.types import ClusterMode, RuntimeVariant

__all__ = (
    "ActivateDeploymentInput",
    "AddRevisionInput",
    "BlueGreenConfigInput",
    "CreateDeploymentInput",
    "DeleteDeploymentInput",
    "ExtraVFolderMountInput",
    "RevisionInput",
    "RollingUpdateConfigInput",
    "ScaleDeploymentInput",
    "UpdateDeploymentInput",
)


class ExtraVFolderMountInput(BaseRequestModel):
    """Input for an extra vfolder mount."""

    vfolder_id: UUID = Field(description="VFolder ID to mount")
    mount_destination: str | None = Field(default=None, description="Mount destination path")


class RollingUpdateConfigInput(BaseRequestModel):
    """Input for rolling update configuration."""

    max_surge: int = Field(
        default=1, ge=0, description="Maximum number of extra replicas during update"
    )
    max_unavailable: int = Field(
        default=0, ge=0, description="Maximum number of unavailable replicas during update"
    )


class BlueGreenConfigInput(BaseRequestModel):
    """Input for blue/green deployment configuration."""

    auto_promote: bool = Field(default=False, description="Automatically promote new revision")
    promote_delay_seconds: int = Field(
        default=0, ge=0, description="Delay in seconds before promotion"
    )


class RevisionInput(BaseRequestModel):
    """Input for a deployment revision."""

    name: str | None = Field(default=None, description="Revision name")
    image_id: UUID = Field(description="Container image ID")
    cluster_mode: ClusterMode = Field(description="Cluster mode for the revision")
    cluster_size: int = Field(default=1, ge=1, description="Number of nodes in the cluster")
    resource_group: str = Field(description="Resource group for allocation")
    resource_slots: Mapping[str, Any] = Field(description="Resource slot requirements")
    resource_opts: Mapping[str, Any] | None = Field(
        default=None, description="Optional resource options"
    )
    runtime_variant: RuntimeVariant = Field(
        default=RuntimeVariant.CUSTOM, description="Runtime variant"
    )
    model_vfolder_id: UUID = Field(description="Model VFolder ID")
    model_mount_destination: str = Field(
        default="/models", description="Mount destination for model vfolder"
    )
    model_definition_path: str = Field(description="Path to model definition file")
    extra_mounts: list[ExtraVFolderMountInput] | None = Field(
        default=None, description="Additional vfolder mounts"
    )
    environ: Mapping[str, str] | None = Field(default=None, description="Environment variables")


class CreateDeploymentInput(BaseRequestModel):
    """Input for creating a deployment."""

    project_id: UUID = Field(description="Project ID")
    domain_name: str = Field(description="Domain name")
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="Deployment name",
    )
    tags: list[str] | None = Field(default=None, description="Deployment tags")
    open_to_public: bool = Field(default=False, description="Whether the deployment is public")
    preferred_domain_name: str | None = Field(
        default=None, description="Preferred domain name for URL"
    )
    strategy: DeploymentStrategy = Field(description="Deployment strategy")
    rollback_on_failure: bool = Field(
        default=False, description="Roll back automatically on failure"
    )
    desired_replica_count: int = Field(ge=0, description="Desired number of replicas")
    initial_revision: RevisionInput = Field(description="Initial revision configuration")
    rolling_update: RollingUpdateConfigInput | None = Field(
        default=None, description="Rolling update config"
    )
    blue_green: BlueGreenConfigInput | None = Field(default=None, description="Blue/green config")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped


class UpdateDeploymentInput(BaseRequestModel):
    """Input for updating a deployment."""

    name: str | None = Field(default=None, description="Updated deployment name")
    desired_replicas: int | None = Field(
        default=None, ge=0, description="Updated desired replica count"
    )
    tags: list[str] | Sentinel | None = Field(
        default=SENTINEL, description="Updated tags. Use SENTINEL to clear."
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped


class DeleteDeploymentInput(BaseRequestModel):
    """Input for deleting a deployment."""

    id: UUID = Field(description="Deployment ID to delete")


class ActivateDeploymentInput(BaseRequestModel):
    """Input for activating a deployment."""

    id: UUID = Field(description="Deployment ID to activate")


class ScaleDeploymentInput(BaseRequestModel):
    """Input for scaling a deployment."""

    id: UUID = Field(description="Deployment ID to scale")
    replicas: int = Field(ge=0, description="Target replica count")


class AddRevisionInput(BaseRequestModel):
    """Input for adding a revision to a deployment."""

    deployment_id: UUID = Field(description="Deployment ID")
    revision: RevisionInput = Field(description="Revision configuration")
