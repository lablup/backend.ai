import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import override

from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass(frozen=True)
class UpdatePasswordNoAuthAction(BaseGlobalAction):
    domain_name: str
    email: str
    current_password: str
    new_password: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GlobalEntityType()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_password_no_auth"


@dataclass(frozen=True)
class UpdatePasswordNoAuthActionResult:
    user_id: uuid.UUID
    password_changed_at: datetime
