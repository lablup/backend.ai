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
    owner_access_key: AccessKey
    enqueue_only: bool
    max_wait_seconds: int
    starts_at: Optional[str]
    reuse_if_exists: bool
    startup_command: Optional[str]
    batch_timeout: Optional[timedelta]
    bootstrap_script: Optional[str]
    dependencies: Optional[list[uuid.UUID]]
    callback_url: Optional[yarl.URL]


@dataclass
class CreateFromParamsAction(SessionAction):
    params: CreateFromParamsActionParams
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
        return "create_from_params"


@dataclass
class CreateFromParamsActionResult(BaseActionResult):
    # TODO: Change this to SessionData
    session_id: uuid.UUID

    # TODO: Add proper type
    result: Mapping[str, Any]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_id)
