"""
Request DTOs for session endpoints.

Each model maps 1:1 to an existing Trafaret schema or manually-parsed
JSON body in ``ai.backend.manager.api.session``.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import AliasChoices, Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.session.types import CustomizedImageVisibilityScope
from ai.backend.common.defs.session import (
    SESSION_PRIORITY_DEFAULT,
    SESSION_PRIORITY_MAX,
    SESSION_PRIORITY_MIN,
)
from ai.backend.common.types import ClusterMode, SessionTypes

__all__ = (
    "CommitSessionRequest",
    "CompleteRequest",
    "ConvertSessionToImageRequest",
    "CreateClusterRequest",
    "CreateFromParamsRequest",
    "CreateFromTemplateRequest",
    "DestroySessionRequest",
    "DownloadFilesRequest",
    "DownloadSingleRequest",
    "ExecuteRequest",
    "GetAbusingReportRequest",
    "GetCommitStatusRequest",
    "GetContainerLogsRequest",
    "GetStatusHistoryRequest",
    "GetTaskLogsRequest",
    "ListFilesRequest",
    "MatchSessionsRequest",
    "RenameSessionRequest",
    "RestartSessionRequest",
    "ShutdownServiceRequest",
    "StartServiceRequest",
    "SyncAgentRegistryRequest",
    "TransitSessionStatusRequest",
)


# ---------------------------------------------------------------------------
# Session creation
# ---------------------------------------------------------------------------


class CreateFromTemplateRequest(BaseRequestModel):
    """POST ``/_/create-from-template``"""

    template_id: UUID | None = Field(
        validation_alias=AliasChoices("template_id", "templateId"),
    )
    session_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("session_name", "name", "clientSessionToken"),
    )
    priority: int = Field(
        default=SESSION_PRIORITY_DEFAULT,
        ge=SESSION_PRIORITY_MIN,
        le=SESSION_PRIORITY_MAX,
    )
    image: str | None = Field(
        default=None,
        validation_alias=AliasChoices("image", "lang"),
    )
    architecture: str | None = Field(
        default=None,
        validation_alias=AliasChoices("architecture", "arch"),
    )
    session_type: SessionTypes | None = Field(
        default=None,
        validation_alias=AliasChoices("session_type", "type", "sessionType"),
    )
    group: str | None = Field(
        default=None,
        validation_alias=AliasChoices("group", "groupName", "group_name"),
    )
    domain: str | None = Field(
        default=None,
        validation_alias=AliasChoices("domain", "domainName", "domain_name"),
    )
    cluster_size: int = Field(
        default=1,
        ge=1,
        validation_alias=AliasChoices("cluster_size", "clusterSize"),
    )
    cluster_mode: ClusterMode = Field(
        default=ClusterMode.SINGLE_NODE,
        validation_alias=AliasChoices("cluster_mode", "clusterMode"),
    )
    config: dict[str, Any] = Field(default_factory=dict)
    tag: str | None = None
    enqueue_only: bool = Field(
        default=False,
        validation_alias=AliasChoices("enqueue_only", "enqueueOnly"),
    )
    max_wait_seconds: int = Field(
        default=0,
        ge=0,
        validation_alias=AliasChoices("max_wait_seconds", "maxWaitSeconds"),
    )
    starts_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("starts_at", "startsAt"),
    )
    batch_timeout: str | None = Field(
        default=None,
        validation_alias=AliasChoices("batch_timeout", "batchTimeout"),
    )
    reuse: bool = Field(
        default=True,
        validation_alias=AliasChoices("reuse", "reuseIfExists"),
    )
    startup_command: str | None = Field(
        default=None,
        validation_alias=AliasChoices("startup_command", "startupCommand"),
    )
    bootstrap_script: str | None = Field(
        default=None,
        validation_alias=AliasChoices("bootstrap_script", "bootstrapScript"),
    )
    dependencies: list[UUID] | list[str] | None = None
    callback_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("callback_url", "callbackUrl", "callbackURL"),
    )
    owner_access_key: str | None = None


class CreateFromParamsRequest(BaseRequestModel):
    """POST ``/`` and POST ``/_/create``"""

    session_name: str = Field(
        validation_alias=AliasChoices("session_name", "name", "clientSessionToken"),
    )
    priority: int = Field(
        default=SESSION_PRIORITY_DEFAULT,
        ge=SESSION_PRIORITY_MIN,
        le=SESSION_PRIORITY_MAX,
    )
    image: str = Field(
        validation_alias=AliasChoices("image", "lang"),
    )
    architecture: str | None = Field(
        default=None,
        validation_alias=AliasChoices("architecture", "arch"),
    )
    session_type: SessionTypes = Field(
        default=SessionTypes.INTERACTIVE,
        validation_alias=AliasChoices("session_type", "type", "sessionType"),
    )
    group: str = Field(
        default="default",
        validation_alias=AliasChoices("group", "groupName", "group_name"),
    )
    domain: str = Field(
        default="default",
        validation_alias=AliasChoices("domain", "domainName", "domain_name"),
    )
    cluster_size: int = Field(
        default=1,
        ge=1,
        validation_alias=AliasChoices("cluster_size", "clusterSize"),
    )
    cluster_mode: ClusterMode = Field(
        default=ClusterMode.SINGLE_NODE,
        validation_alias=AliasChoices("cluster_mode", "clusterMode"),
    )
    config: dict[str, Any] = Field(default_factory=dict)
    tag: str | None = None
    enqueue_only: bool = Field(
        default=False,
        validation_alias=AliasChoices("enqueue_only", "enqueueOnly"),
    )
    max_wait_seconds: int = Field(
        default=0,
        ge=0,
        validation_alias=AliasChoices("max_wait_seconds", "maxWaitSeconds"),
    )
    starts_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("starts_at", "startsAt"),
    )
    batch_timeout: str | None = Field(
        default=None,
        validation_alias=AliasChoices("batch_timeout", "batchTimeout"),
    )
    reuse: bool = Field(
        default=True,
        validation_alias=AliasChoices("reuse", "reuseIfExists"),
    )
    startup_command: str | None = Field(
        default=None,
        validation_alias=AliasChoices("startup_command", "startupCommand"),
    )
    bootstrap_script: str | None = Field(
        default=None,
        validation_alias=AliasChoices("bootstrap_script", "bootstrapScript"),
    )
    dependencies: list[UUID] | list[str] | None = None
    callback_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("callback_url", "callbackUrl", "callbackURL"),
    )
    owner_access_key: str | None = None


class CreateClusterRequest(BaseRequestModel):
    """POST ``/_/create-cluster``"""

    session_name: str = Field(
        validation_alias=AliasChoices("session_name", "clientSessionToken"),
    )
    template_id: UUID | None = Field(
        validation_alias=AliasChoices("template_id", "templateId"),
    )
    session_type: SessionTypes = Field(
        default=SessionTypes.INTERACTIVE,
        validation_alias=AliasChoices("session_type", "type", "sessionType"),
    )
    group: str = Field(
        default="default",
        validation_alias=AliasChoices("group", "groupName", "group_name"),
    )
    domain: str = Field(
        default="default",
        validation_alias=AliasChoices("domain", "domainName", "domain_name"),
    )
    scaling_group: str | None = Field(
        default=None,
        validation_alias=AliasChoices("scaling_group", "scalingGroup"),
    )
    tag: str | None = None
    enqueue_only: bool = Field(
        default=False,
        validation_alias=AliasChoices("enqueue_only", "enqueueOnly"),
    )
    max_wait_seconds: int = Field(
        default=0,
        ge=0,
        validation_alias=AliasChoices("max_wait_seconds", "maxWaitSeconds"),
    )
    owner_access_key: str | None = None


# ---------------------------------------------------------------------------
# Service management
# ---------------------------------------------------------------------------


class StartServiceRequest(BaseRequestModel):
    """POST ``/{session_name}/start-service``"""

    login_session_token: str | None = None
    app: str = Field(
        validation_alias=AliasChoices("app", "service"),
    )
    port: int | None = Field(default=None, ge=1024, le=65535)
    envs: str | None = None
    arguments: str | None = None


class ShutdownServiceRequest(BaseRequestModel):
    """POST ``/{session_name}/shutdown-service``"""

    service_name: str


# ---------------------------------------------------------------------------
# Commit / imagify
# ---------------------------------------------------------------------------


class GetCommitStatusRequest(BaseRequestModel):
    """GET ``/{session_name}/commit``"""

    login_session_token: str | None = None


class CommitSessionRequest(BaseRequestModel):
    """POST ``/{session_name}/commit``"""

    login_session_token: str | None = None
    filename: str | None = Field(
        default=None,
        validation_alias=AliasChoices("filename", "fname"),
    )


class ConvertSessionToImageRequest(BaseRequestModel):
    """POST ``/{session_name}/imagify``"""

    image_name: str = Field(pattern=r"^[a-zA-Z0-9.\-_]+$")
    login_session_token: str | None = None
    image_visibility: CustomizedImageVisibilityScope = Field(
        default=CustomizedImageVisibilityScope.USER,
    )


# ---------------------------------------------------------------------------
# Status / transit
# ---------------------------------------------------------------------------


class GetAbusingReportRequest(BaseRequestModel):
    """GET ``/{session_name}/abusing-report``"""

    login_session_token: str | None = None


class SyncAgentRegistryRequest(BaseRequestModel):
    """POST ``/_/sync-agent-registry``"""

    agent: str


class TransitSessionStatusRequest(BaseRequestModel):
    """POST ``/_/transit-status``"""

    ids: list[UUID] = Field(
        validation_alias=AliasChoices("ids", "session_ids", "sessionIds", "SessionIds"),
    )


# ---------------------------------------------------------------------------
# Session lifecycle
# ---------------------------------------------------------------------------


class RenameSessionRequest(BaseRequestModel):
    """POST ``/{session_name}/rename``"""

    session_name: str = Field(
        validation_alias=AliasChoices("session_name", "name", "clientSessionToken"),
    )


class DestroySessionRequest(BaseRequestModel):
    """DELETE ``/{session_name}``"""

    forced: bool = False
    recursive: bool = False
    owner_access_key: str | None = None


class RestartSessionRequest(BaseRequestModel):
    """PATCH ``/{session_name}``"""

    owner_access_key: str | None = None


class MatchSessionsRequest(BaseRequestModel):
    """GET ``/_/match``"""

    id: str


# ---------------------------------------------------------------------------
# Code execution
# ---------------------------------------------------------------------------


class ExecuteRequest(BaseRequestModel):
    """POST ``/{session_name}``"""

    mode: str | None = None
    run_id: str | None = None
    code: str | None = None
    options: dict[str, Any] | None = None


class CompleteRequest(BaseRequestModel):
    """POST ``/{session_name}/complete``"""

    code: str | None = None
    options: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------


class DownloadFilesRequest(BaseRequestModel):
    """POST ``/{session_name}/download``"""

    files: list[str]


class DownloadSingleRequest(BaseRequestModel):
    """POST ``/{session_name}/download_single``"""

    file: str


class ListFilesRequest(BaseRequestModel):
    """GET ``/{session_name}/files``"""

    path: str = "."


# ---------------------------------------------------------------------------
# Logs / history
# ---------------------------------------------------------------------------


class GetContainerLogsRequest(BaseRequestModel):
    """GET ``/{session_name}/logs``"""

    owner_access_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("owner_access_key", "ownerAccessKey"),
    )
    kernel_id: UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("kernel_id", "kernelId"),
    )


class GetTaskLogsRequest(BaseRequestModel):
    """HEAD/GET ``/_/logs``"""

    kernel_id: UUID = Field(
        validation_alias=AliasChoices(
            "kernel_id", "session_name", "sessionName", "task_id", "taskId"
        ),
    )


class GetStatusHistoryRequest(BaseRequestModel):
    """GET ``/{session_name}/status-history``"""

    owner_access_key: str | None = None
