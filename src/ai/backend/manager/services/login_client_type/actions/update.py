from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.login_client_type import LOGIN_CLIENT_TYPE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import UpdateGlobalOpsAction
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.repositories.login_client_type.updaters import LoginClientTypeUpdater


@dataclass
class UpdateLoginClientTypeAction(UpdateGlobalOpsAction[LoginClientTypeRow, LoginClientTypeData]):
    """Rename a login client type or retouch its description."""

    updater: LoginClientTypeUpdater

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return LOGIN_CLIENT_TYPE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_login_client_type"

    @override
    def to_updater(self) -> LoginClientTypeUpdater:
        return self.updater
