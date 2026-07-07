from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import AccessKey, ClusterMode, MountInfoEntry, SessionTypes
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.base import SessionScopeAction


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
    is_preemptible: bool = True
    dependencies: list[uuid.UUID] | None = None
    agent_list: list[str] | None = None
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

    RBAC validation checks if the user has CREATE permission in USER scope.
    """

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
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.owner_id) if self.owner_id is not None else str(self.user_id)

    @override
    def target_element(self) -> RBACElementRef:
        # When delegating (owner_id set), authorize the caller against the
        # *owner's* USER scope, not the caller's own — otherwise the check
        # trivially passes and delegation is unguarded.
        target_user_id = self.owner_id if self.owner_id is not None else self.user_id
        return RBACElementRef(
            element_type=RBACElementType.USER,
            element_id=str(target_user_id),
        )


@dataclass
class EnqueueSessionActionResult(BaseActionResult):
    """Returns full session data for SessionNode conversion."""

    session_data: SessionData

    @override
    def entity_id(self) -> str | None:
        return str(self.session_data.id)
