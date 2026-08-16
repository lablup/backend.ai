from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.login_client_type import LoginClientTypeID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.repositories.login_client_type.queriers import LoginClientTypeQuerier


@dataclass
class GetLoginClientTypeAction(GetSingleEntityOpsAction[LoginClientTypeRow, LoginClientTypeData]):
    """Read one login client type; every authenticated user may."""

    id: LoginClientTypeID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_login_client_type"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.id

    @override
    def to_querier(self) -> LoginClientTypeQuerier:
        return LoginClientTypeQuerier(login_client_type_id=self.id)
