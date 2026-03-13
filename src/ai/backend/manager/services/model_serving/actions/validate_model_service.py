import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import AccessKey, RuntimeVariant, VFolderMount
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.types import ServiceConfig
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class ValidateModelServiceAction(ModelServiceAction):
    requester_access_key: AccessKey
    owner_access_key: AccessKey
    requester_uuid: uuid.UUID
    requester_role: UserRole
    requester_domain: str
    keypair_resource_policy: dict[str, Any]
    domain_name: str
    group_name: str
    config: ServiceConfig
    replicas: int
    runtime_variant: RuntimeVariant
    max_session_count_per_model_session: int
    owner_access_key_override: AccessKey | None

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class ValidateModelServiceActionResult(BaseActionResult):
    model_id: uuid.UUID
    model_definition_path: str | None
    requester_access_key: AccessKey
    owner_access_key: AccessKey
    owner_uuid: uuid.UUID
    owner_role: UserRole
    group_id: uuid.UUID
    resource_policy: dict[str, Any]
    scaling_group: str
    extra_mounts: Sequence[VFolderMount]

    @override
    def entity_id(self) -> str | None:
        return None
