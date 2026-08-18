from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdateSingleEntityOpsAction
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.login_client_type.updaters import LoginClientTypeUpdater


@dataclass
class UpdateLoginClientTypeAction(
    UpdateSingleEntityOpsAction[LoginClientTypeRow, LoginClientTypeData]
):
    """Rename a login client type or retouch its description."""

    updater: LoginClientTypeUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_login_client_type"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.login_client_type_id

    @override
    def to_updater(self) -> LoginClientTypeUpdater:
        return self.updater
