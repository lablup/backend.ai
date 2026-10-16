from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdatePartialBulkOpsAction
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.login_client_type.updaters import LoginClientTypeUpdater


@dataclass(frozen=True)
class PartialBulkUpdateLoginClientTypesAction(
    UpdatePartialBulkOpsAction[LoginClientTypeRow, LoginClientTypeData]
):
    """Rename or retouch the named login client types, answering for each one."""

    updaters: Sequence[LoginClientTypeUpdater]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_update_login_client_types"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(updater.login_client_type_id for updater in self.updaters)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, LoginClientTypeUpdater]:
        return {updater.login_client_type_id: updater for updater in self.updaters}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self,
            updaters=[
                updater for updater in self.updaters if updater.login_client_type_id in allowed
            ],
        )
