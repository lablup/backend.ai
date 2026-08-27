import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE, PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.types import AccessKey, SessionTypes
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.base import (
    SessionScopeAction,
    SessionScopeActionResult,
)


@dataclass
class CreateClusterAction(SessionScopeAction):
    """Create a new cluster session.

    Answered for by the project the session is created in.
    """

    project_id: ProjectID

    session_name: str
    user_id: uuid.UUID
    user_role: UserRole
    sudo_session_enabled: bool
    template_id: uuid.UUID
    session_type: SessionTypes
    group_name: str
    domain_name: str
    resource_group_name: str
    requester_access_key: AccessKey
    owner_access_key: AccessKey
    tag: str
    enqueue_only: bool
    keypair_resource_policy: dict[str, Any] | None
    max_wait_seconds: int

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
        return "create_cluster"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateClusterActionResult(SessionScopeActionResult):
    # TODO: Change this to SessionData
    session_id: uuid.UUID

    # TODO: Add proper type
    result: Mapping[str, Any]
