import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, override

import yarl

from ai.backend.common.types import AccessKey, ClusterMode, SessionTypes
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
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
    starts_at: str | None
    reuse_if_exists: bool
    startup_command: str | None
    batch_timeout: timedelta | None
    bootstrap_script: str | None | Undefined
    dependencies: list[uuid.UUID] | None
    callback_url: yarl.URL | None


@dataclass
class CreateFromTemplateAction(SessionAction):
    params: CreateFromTemplateActionParams
    user_id: uuid.UUID
    user_role: UserRole
    sudo_session_enabled: bool
    requester_access_key: AccessKey
    keypair_resource_policy: dict[str, Any] | None

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateFromTemplateActionResult(BaseActionResult):
    session_id: uuid.UUID

    # TODO: Add proper type
    result: Mapping[str, Any]

    @override
    def entity_id(self) -> str | None:
        return str(self.session_id)
