from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.login_client_type import LOGIN_CLIENT_TYPE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalOpsAction
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.creators import LoginClientTypeCreator
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow


@dataclass
class CreateLoginClientTypeAction(CreateGlobalOpsAction[LoginClientTypeRow, LoginClientTypeData]):
    """Register a login client type in the global catalog."""

    creator: LoginClientTypeCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return LOGIN_CLIENT_TYPE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_login_client_type"

    @override
    def to_creator(self) -> LoginClientTypeCreator:
        return self.creator
