from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.login_client_type import LoginClientTypeID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeEntityOpsAction
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.purgers import LoginClientTypePurger
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow


@dataclass(frozen=True)
class PartialBulkPurgeLoginClientTypesAction(
    PartialBulkPurgeEntityOpsAction[LoginClientTypeRow, LoginClientTypeData]
):
    """Remove the named login client types from the catalog, answering for each one."""

    ids: Sequence[LoginClientTypeID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_login_client_types"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, LoginClientTypePurger]:
        return {
            type_id: LoginClientTypePurger(login_client_type_id=type_id) for type_id in self.ids
        }

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[type_id for type_id in self.ids if type_id in allowed])
