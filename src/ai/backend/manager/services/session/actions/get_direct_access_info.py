from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class GetDirectAccessInfoAction(SessionAction):
    session_name: str
    owner_access_key: AccessKey

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION_DIRECT_ACCESS

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetDirectAccessInfoActionResult(BaseActionResult):
    # TODO: Add proper type
    result: Any
    session_data: SessionData

    @override
    def entity_id(self) -> str | None:
        return str(self.session_data.id)
