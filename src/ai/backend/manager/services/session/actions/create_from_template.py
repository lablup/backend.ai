import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Mapping, Optional, override

import yarl

from ai.backend.common.types import AccessKey, ClusterMode, SessionTypes
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.base import SessionAction


# TODO: Idea: Refactor this type using pydantic and utilize as API model
@dataclass
class CreateFromTemplateActionParams:
    template_id: uuid.UUID
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
    owner_access_key: AccessKey
    enqueue_only: bool = False
    max_wait_seconds: int = 0
    starts_at: Optional[str] = None
    reuse_if_exists: bool = True
    startup_command: Optional[str] = None
    batch_timeout: Optional[timedelta] = None
    bootstrap_script: Optional[str] = None
    dependencies: Optional[list[uuid.UUID]] = None
    callback_url: Optional[yarl.URL] = None


@dataclass
class CreateFromTemplateAction(SessionAction):
    params: CreateFromTemplateActionParams
    user_id: uuid.UUID
    user_role: UserRole
    sudo_session_enabled: bool
    requester_access_key: AccessKey
    agent_list: Optional[list[str]] = None
    keypair_resource_policy: Optional[dict] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "create_from_template"


@dataclass
class CreateFromTemplateActionResult(BaseActionResult):
    session_id: uuid.UUID

    # TODO: Add proper type
    result: Mapping[str, Any]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_id)
