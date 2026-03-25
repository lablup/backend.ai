"""Shared path parameter DTOs for v2 REST endpoints."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class DomainNamePathParam(BaseRequestModel):
    domain_name: str = Field(description="Domain name")


class UserIdPathParam(BaseRequestModel):
    user_id: UUID = Field(description="User UUID")


class ProjectIdPathParam(BaseRequestModel):
    project_id: UUID = Field(description="Project UUID")


class AgentIdPathParam(BaseRequestModel):
    agent_id: str = Field(description="Agent ID")


class SessionIdPathParam(BaseRequestModel):
    session_id: UUID = Field(description="Session UUID")


class StorageIdPathParam(BaseRequestModel):
    storage_id: UUID = Field(description="Storage UUID")


class RegistryIdPathParam(BaseRequestModel):
    registry_id: UUID = Field(description="Registry UUID")


class ArtifactIdPathParam(BaseRequestModel):
    artifact_id: UUID = Field(description="Artifact UUID")


class RevisionIdPathParam(BaseRequestModel):
    revision_id: UUID = Field(description="Revision UUID")


class DeploymentIdPathParam(BaseRequestModel):
    deployment_id: UUID = Field(description="Deployment UUID")


class RoleIdPathParam(BaseRequestModel):
    role_id: UUID = Field(description="Role UUID")


class PermissionIdPathParam(BaseRequestModel):
    permission_id: UUID = Field(description="Permission UUID")


class ResourceGroupNamePathParam(BaseRequestModel):
    name: str = Field(description="Resource group name")


class ChannelIdPathParam(BaseRequestModel):
    channel_id: UUID = Field(description="Channel UUID")


class RuleIdPathParam(BaseRequestModel):
    rule_id: UUID = Field(description="Rule UUID")


class PresetIdPathParam(BaseRequestModel):
    preset_id: UUID = Field(description="Preset UUID")


class ReplicaIdPathParam(BaseRequestModel):
    replica_id: UUID = Field(description="Replica UUID")


class RouteIdPathParam(BaseRequestModel):
    route_id: UUID = Field(description="Route UUID")
