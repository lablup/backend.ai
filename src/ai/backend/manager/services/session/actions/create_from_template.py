import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Mapping, Optional, override

import yarl

from ai.backend.common.types import AccessKey, ClusterMode, SessionTypes
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.api.utils import Undefined
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.base import SessionAction


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
    owner_access_key: AccessKey | Undefined
    enqueue_only: bool
    max_wait_seconds: int
    starts_at: Optional[str]
    reuse_if_exists: bool
    startup_command: Optional[str]
    batch_timeout: Optional[timedelta]
    bootstrap_script: Optional[str] | Undefined
    dependencies: Optional[list[uuid.UUID]]
    callback_url: Optional[yarl.URL]


@dataclass
class CreateFromTemplateAction(SessionAction):
    params: CreateFromTemplateActionParams
    user_id: uuid.UUID
    user_role: UserRole
    sudo_session_enabled: bool
    requester_access_key: AccessKey
    keypair_resource_policy: Optional[dict]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create_from_template"


@dataclass
class CreateFromTemplateActionResult(BaseActionResult):
    session_id: uuid.UUID

    # TODO: Add proper type
    result: Mapping[str, Any]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_id)
