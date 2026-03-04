import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.common.types import AccessKey, SessionTypes
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.base import SessionScopeAction


@dataclass
class CreateClusterAction(SessionScopeAction):
    """Create a new cluster session within a scope (domain/project).

    The scope is determined by group_id (PROJECT scope) or domain_name (DOMAIN scope).
    RBAC validation checks if the user has CREATE permission in the target scope.
    """

    session_name: str
    user_id: uuid.UUID
    user_role: UserRole
    sudo_session_enabled: bool
    template_id: uuid.UUID
    session_type: SessionTypes
    group_name: str
    domain_name: str
    scaling_group_name: str
    requester_access_key: AccessKey
    owner_access_key: AccessKey
    tag: str
    enqueue_only: bool
    keypair_resource_policy: dict[str, Any] | None
    max_wait_seconds: int
    _scope_type: ScopeType = ScopeType.GLOBAL  # TODO: Set from context
    _scope_id: str = ""  # TODO: Set from context

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def scope_type(self) -> ScopeType:
        return self._scope_type

    @override
    def scope_id(self) -> str:
        return self._scope_id

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType(self._scope_type.value),
            element_id=self._scope_id,
        )


@dataclass
class CreateClusterActionResult(BaseActionResult):
    # TODO: Change this to SessionData
    session_id: uuid.UUID

    # TODO: Add proper type
    result: Mapping[str, Any]

    @override
    def entity_id(self) -> str | None:
        return str(self.session_id)
