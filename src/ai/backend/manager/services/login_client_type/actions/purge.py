from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.login_client_type import (
    LOGIN_CLIENT_TYPE_ENTITY_TYPE,
    LoginClientTypeID,
)
from ai.backend.common.data.entity.types import EntityID, EntityType
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.purgers import LoginClientTypePurger
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow


@dataclass
class PurgeLoginClientTypeAction(PurgeEntityOpsAction[LoginClientTypeRow, LoginClientTypeData]):
    """Remove a login client type from the catalog.

    Purge-shaped: the table carries no lifecycle column, so deleting one has always
    been the row leaving the table.
    """

    id: UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return LOGIN_CLIENT_TYPE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_login_client_type"

    @override
    def entity_id(self) -> EntityID:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> LoginClientTypePurger:
        return LoginClientTypePurger(login_client_type_id=LoginClientTypeID(self.id))
