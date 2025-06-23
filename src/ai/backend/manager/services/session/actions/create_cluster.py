import uuid
from dataclasses import dataclass
from typing import Any, Mapping, Optional, override

from ai.backend.common.types import AccessKey, SessionTypes
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class CreateClusterAction(SessionAction):
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
    keypair_resource_policy: Optional[dict]
    max_wait_seconds: int

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create_cluster"


@dataclass
class CreateClusterActionResult(BaseActionResult):
    # TODO: Change this to SessionData
    session_id: uuid.UUID

    # TODO: Add proper type
    result: Mapping[str, Any]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_id)
