import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, override

import yarl

from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.common.defs.session import JOB_PRIORITY_DEFAULT
from ai.backend.common.types import AccessKey, ClusterMode, SessionTypes
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.base import (
    SessionScopeAction,
    SessionScopeActionResult,
)


# TODO: Idea: Refactor this type using pydantic and utilize as API model
@dataclass
class CreateFromParamsActionParams:
    session_name: str
    image: str
    architecture: str
    session_type: SessionTypes
    group_name: str
    domain_name: str
    cluster_size: int
    cluster_mode: ClusterMode
    config: dict[str, Any]
    tag: str
    priority: int
    is_preemptible: bool
    owner_access_key: AccessKey
    enqueue_only: bool
    max_wait_seconds: int
    starts_at: str | None
    reuse_if_exists: bool
    startup_command: str | None
    batch_timeout: timedelta | None
    bootstrap_script: str | None
    dependencies: list[uuid.UUID] | None
    callback_url: yarl.URL | None
    # Scope-local preemption priority (ranks the requester's own sessions).
    job_priority: int = JOB_PRIORITY_DEFAULT


@dataclass
class CreateFromParamsAction(SessionScopeAction):
    """Create a new session from parameters.

    Answered for by the project the session is created in.
    """

    project_id: ProjectID

    params: CreateFromParamsActionParams
    user_id: uuid.UUID
    user_role: UserRole
    sudo_session_enabled: bool
    requester_access_key: AccessKey
    keypair_resource_policy: dict[str, Any] | None

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=self.project_id),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_from_params"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateFromParamsActionResult(SessionScopeActionResult):
    # TODO: Change this to SessionData
    session_id: uuid.UUID

    # TODO: Add proper type
    result: Mapping[str, Any]
