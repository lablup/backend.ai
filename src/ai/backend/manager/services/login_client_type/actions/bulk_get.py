from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.login_client_type import LoginClientTypeID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.queriers import BulkLoginClientTypeQuerier
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow


@dataclass
class BulkGetLoginClientTypesAction(
    PartialBulkGetEntityOpsAction[LoginClientTypeRow, LoginClientTypeData]
):
    """Read the login client types the caller named, one permission check per type."""

    ids: Sequence[LoginClientTypeID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_login_client_types"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkLoginClientTypeQuerier:
        return BulkLoginClientTypeQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
