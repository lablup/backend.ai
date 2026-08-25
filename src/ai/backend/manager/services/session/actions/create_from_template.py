import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, override

import yarl

from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE, PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.defs.session import JOB_PRIORITY_DEFAULT
from ai.backend.common.types import AccessKey, ClusterMode, SessionTypes
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.common.sentinel import Undefined
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.base import (
    SessionScopeAction,
    SessionScopeActionResult,
)


# TODO: Idea: Refactor this type using pydantic and utilize as API model
# TODO: Remove Undefined before passing to Service layer
@dataclass
class CreateFromTemplateActionParams:
    template_id: uuid.UUID
    session_name: str | Undefined
    image: str | Undefined
    architecture: str | Undefined
    session_type: SessionTypes | Undefined
    group_name: str | Undefined
    domain_name: str | Undefined
    cluster_size: int
    cluster_mode: ClusterMode
    config: dict[str, Any]
    tag: str | Undefined
    priority: int
    is_preemptible: bool
    owner_access_key: AccessKey | Undefined
    enqueue_only: bool
    max_wait_seconds: int
    starts_at: str | None
    reuse_if_exists: bool
    startup_command: str | None
    batch_timeout: timedelta | None
    bootstrap_script: str | None | Undefined
    dependencies: list[uuid.UUID] | None
    callback_url: yarl.URL | None
    # Scope-local preemption priority (ranks the requester's own sessions).
    job_priority: int = JOB_PRIORITY_DEFAULT


@dataclass
class CreateFromTemplateAction(SessionScopeAction):
    """Create a new session from template.

    Answered for by the project the session is created in.
    """

    project_id: ProjectID

    params: CreateFromTemplateActionParams
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
    def available_scope_types(cls) -> Sequence[EntityType]:
        return (PROJECT_ENTITY_TYPE,)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_from_template"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateFromTemplateActionResult(SessionScopeActionResult):
    session_id: uuid.UUID

    # TODO: Add proper type
    result: Mapping[str, Any]
