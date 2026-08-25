from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import override

from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE, PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.defs.session import JOB_PRIORITY_DEFAULT
from ai.backend.common.types import AccessKey, ClusterMode, MountInfoEntry, SessionTypes
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.base import (
    SessionScopeAction,
    SessionScopeActionResult,
)


@dataclass(frozen=True)
class ResourceSlotEntry:
    """A single resource slot allocation entry."""

    resource_type: str
    quantity: str


@dataclass(frozen=True)
class SessionResourceSpec:
    """Compute resource allocation and cluster configuration."""

    entries: list[ResourceSlotEntry]
    resource_group: str | None = None
    resource_group_id: ResourceGroupID | None = None
    shmem: str | None = None
    cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE
    cluster_size: int = 1


@dataclass(frozen=True)
class SessionExecutionSpec:
    """Container runtime environment configuration."""

    environ: dict[str, str] | None = None
    preopen_ports: list[int] | None = None
    bootstrap_script: str | None = None


@dataclass(frozen=True)
class SessionSchedulingSpec:
    """Scheduling constraints and preferences."""

    priority: int = 10
    job_priority: int = JOB_PRIORITY_DEFAULT
    is_preemptible: bool = True
    dependencies: list[uuid.UUID] | None = None
    agent_list: list[str] | None = None
    agent_selection_policy: AgentSelectionPolicy | None = None
    attach_network: uuid.UUID | None = None


@dataclass(frozen=True)
class SessionBatchSpec:
    """Batch session specific configuration. Required for BATCH sessions."""

    startup_command: str
    starts_at: datetime | None = None
    batch_timeout: timedelta | None = None


@dataclass
class EnqueueSessionAction(SessionScopeAction):
    """Enqueue a new compute session (interactive or batch) for scheduling.

    The session is placed in PENDING status immediately.
    The scheduler picks it up asynchronously for resource allocation and launch.

    Answered for by the project the session is created in.
    """

    project_id: ProjectID

    session_name: str
    session_type: SessionTypes
    image_id: uuid.UUID

    resource: SessionResourceSpec
    scheduling: SessionSchedulingSpec
    mounts: list[MountInfoEntry] | None = None
    execution: SessionExecutionSpec | None = None
    batch: SessionBatchSpec | None = None

    tag: str | None = None
    callback_url: str | None = None

    user_id: uuid.UUID = field(default_factory=lambda: uuid.UUID(int=0))
    user_role: UserRole = UserRole.USER
    access_key: AccessKey = AccessKey("")
    domain_name: str = ""
    group_id: uuid.UUID = field(default_factory=lambda: uuid.UUID(int=0))
    owner_id: uuid.UUID | None = None
    """Delegated owner user UUID. When set, the service resolves it and
    overrides ``user_id``, ``user_role``, ``access_key``, and ``domain_name``
    with the target user's values.
    """

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=self.project_id),)

    @override
    @classmethod
    def available_scope_types(cls) -> Sequence[EntityType]:
        return (PROJECT_ENTITY_TYPE,)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "enqueue_session"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class EnqueueSessionActionResult(SessionScopeActionResult):
    """Returns full session data for SessionNode conversion."""

    session_data: SessionData
